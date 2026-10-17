"""
blueprints/users.py — zarządzanie kontami przez administratora (US-009, FR-022, R-07).

  GET   /api/admin/users              lista kont
  POST  /api/admin/users              nowe konto + link do ustawienia hasła (bez hasła w e-mailu)
  PATCH /api/admin/users/<id>         rola / aktywność / dział / e-mail
  POST  /api/admin/users/<id>/invite  ponowny link ustawienia hasła

Zasady: tylko rola admin, CSRF na mutacjach, audyt każdej zmiany, ochrona ostatniego
aktywnego administratora, admin nie dezaktywuje i nie degraduje samego siebie.
Blueprint → core/db (nigdy → app); wysyłkę e-maila wstrzykuje app przez
current_app.config["SEND_PASSWORD_LINK"] (callable: to_email, username, url → bool).
"""

from __future__ import annotations

import os
import re
import secrets

from flask import Blueprint, current_app, jsonify, request, session
from werkzeug.security import generate_password_hash

from constants import INVITE_TOKEN_TTL_HOURS, VALID_ROLES
from core.accounts import issue_password_token
from core.audit import log_audit
from core.security import csrf_protect, require_role
from db import IntegrityError, get_db

bp = Blueprint("users", __name__)

_USERNAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,49}$")
_EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}\.[^@\s]{2,63}$")
_PUBLIC_COLS = "id, username, email, role, COALESCE(is_active,1) AS is_active, department, created_at, last_login"


def _row(db, uid: int):
    # Bandit B608: interpolowana jest stała lista kolumn z kodu, wartości jako parametry.
    return db.execute(f"SELECT {_PUBLIC_COLS} FROM users WHERE id=?", (uid,)).fetchone()  # nosec B608


def _active_admins_except(db, uid: int) -> int:
    return db.execute(
        "SELECT COUNT(*) FROM users WHERE role='admin' AND COALESCE(is_active,1)=1 AND id<>?",
        (uid,),
    ).fetchone()[0]


def _send_link(db, user_id: int, username: str, email: str) -> dict:
    """Wystawia token (24 h) i wysyła link. Gdy e-mail niedostępny — zwraca link adminowi,
    który przekazuje go użytkownikowi bezpiecznym kanałem."""
    token = issue_password_token(db, user_id, INVITE_TOKEN_TTL_HOURS)
    db.commit()
    base = os.environ.get("APP_BASE_URL") or request.host_url.rstrip("/")
    url = f"{base}/reset-password?token={token}"
    sender = current_app.config.get("SEND_PASSWORD_LINK")
    sent = bool(email and sender and sender(email, username, url))
    return {"invite_sent": sent, **({} if sent else {"setup_url": url})}


@bp.route("/api/admin/users", methods=["GET"])
@require_role("admin")
def api_users_list():
    db = get_db()
    try:
        rows = db.execute(f"SELECT {_PUBLIC_COLS} FROM users ORDER BY username").fetchall()  # nosec B608
        return jsonify([dict(r) for r in rows])
    finally:
        db.close()


@bp.route("/api/admin/users", methods=["POST"])
@require_role("admin")
@csrf_protect
def api_users_create():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username") or "").strip()
    email = str(data.get("email") or "").strip().lower()
    role = str(data.get("role") or "user").strip()
    department = str(data.get("department") or "").strip()[:100]
    if not _USERNAME_RE.match(username):
        return jsonify({"error": "Nazwa użytkownika: 3–50 znaków (litery, cyfry, . _ -)."}), 400
    if email and not _EMAIL_RE.match(email):
        return jsonify({"error": "Nieprawidłowy adres e-mail."}), 400
    if role not in VALID_ROLES:
        return jsonify({"error": "Nieprawidłowa rola."}), 400
    db = get_db()
    try:
        dup = db.execute(
            "SELECT 1 FROM users WHERE LOWER(username)=LOWER(?) OR (?<>'' AND LOWER(email)=LOWER(?))",
            (username, email, email),
        ).fetchone()
        if dup:
            return jsonify({"error": "Konto o tej nazwie lub adresie e-mail już istnieje."}), 409
        # Hasło losowe i nieznane nikomu — użytkownik ustawia własne przez link (US-009).
        cur = db.execute(
            "INSERT INTO users(username, email, password_hash, role, department, is_active) "
            "VALUES (?,?,?,?,?,1)",
            (
                username,
                email or None,
                generate_password_hash(secrets.token_urlsafe(32)),
                role,
                department,
            ),
        )
        db.commit()
        uid = cur.lastrowid or _row_id(db, username)
        link = _send_link(db, uid, username, email)
    except IntegrityError:
        db.rollback()
        return jsonify({"error": "Konto o tej nazwie już istnieje."}), 409
    finally:
        db.close()
    log_audit("user_create", session.get("username"), f"{username} rola={role} dział={department}")
    return jsonify({"ok": True, "id": uid, **link}), 201


def _row_id(db, username):
    r = db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
    return r[0] if r else None


@bp.route("/api/admin/users/<int:uid>", methods=["PATCH"])
@require_role("admin")
@csrf_protect
def api_users_update(uid):
    data = request.get_json(silent=True) or {}
    me = session.get("user_id")
    db = get_db()
    try:
        user = _row(db, uid)
        if not user:
            return jsonify({"error": "Nie znaleziono konta."}), 404
        sets, params, changes = [], [], []
        if "role" in data:
            role = str(data.get("role") or "").strip()
            if role not in VALID_ROLES:
                return jsonify({"error": "Nieprawidłowa rola."}), 400
            if role != user["role"]:
                if uid == me:
                    return jsonify({"error": "Nie możesz zmienić własnej roli."}), 400
                if user["role"] == "admin" and _active_admins_except(db, uid) == 0:
                    return jsonify(
                        {"error": "To ostatni aktywny administrator — nie można zmienić roli."}
                    ), 409
                sets.append("role=?")
                params.append(role)
                changes.append(f"rola {user['role']}→{role}")
        if "is_active" in data:
            active = 1 if data.get("is_active") in (True, 1, "1", "true") else 0
            if active != int(user["is_active"]):
                if uid == me:
                    return jsonify({"error": "Nie możesz dezaktywować własnego konta."}), 400
                if not active and user["role"] == "admin" and _active_admins_except(db, uid) == 0:
                    return jsonify(
                        {"error": "To ostatni aktywny administrator — nie można go dezaktywować."}
                    ), 409
                sets.append("is_active=?")
                params.append(active)
                changes.append("aktywowane" if active else "dezaktywowane")
        if "department" in data:
            sets.append("department=?")
            params.append(str(data.get("department") or "").strip()[:100])
            changes.append("dział")
        if "email" in data:
            email = str(data.get("email") or "").strip().lower()
            if email and not _EMAIL_RE.match(email):
                return jsonify({"error": "Nieprawidłowy adres e-mail."}), 400
            sets.append("email=?")
            params.append(email or None)
            changes.append("e-mail")
        if not sets:
            return jsonify({"ok": True, "user": dict(user)})
        params.append(uid)
        # Bandit B608: nazwy kolumn z twardej białej listy (role/is_active/department/email), wartości jako parametry.
        db.execute(f"UPDATE users SET {', '.join(sets)} WHERE id=?", params)  # nosec B608
        if any(c == "dezaktywowane" for c in changes):
            # dezaktywacja unieważnia też otwarte linki ustawienia hasła
            db.execute("UPDATE password_reset_tokens SET used=1 WHERE user_id=? AND used=0", (uid,))
        db.commit()
        updated = dict(_row(db, uid))
    finally:
        db.close()
    log_audit("user_update", session.get("username"), f"{user['username']}: {', '.join(changes)}")
    return jsonify({"ok": True, "user": updated})


@bp.route("/api/admin/users/<int:uid>/invite", methods=["POST"])
@require_role("admin")
@csrf_protect
def api_users_invite(uid):
    db = get_db()
    try:
        user = _row(db, uid)
        if not user:
            return jsonify({"error": "Nie znaleziono konta."}), 404
        if not int(user["is_active"]):
            return jsonify({"error": "Konto jest nieaktywne."}), 409
        link = _send_link(db, uid, user["username"], user["email"] or "")
    finally:
        db.close()
    log_audit(
        "user_invite", session.get("username"), f"link ustawienia hasła dla {user['username']}"
    )
    return jsonify({"ok": True, **link})
