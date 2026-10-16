"""
core/accounts.py — wspólne operacje na kontach (US-009): tokeny ustawienia/resetu hasła.

Tokeny w bazie wyłącznie jako SHA-256 (US-003, SEC-002). Używane przez app.py (reset hasła)
i blueprints/users.py (zaproszenie nowego konta). Zależy tylko od standardowej biblioteki.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone


def hash_reset_token(token: str) -> str:
    """SHA-256 tokenu resetu/zaproszenia — w bazie trzymamy tylko hash."""
    return hashlib.sha256(str(token or "").encode("utf-8")).hexdigest()


def issue_password_token(db, user_id: int, ttl_hours: float) -> str:
    """Unieważnia niewykorzystane tokeny konta, zapisuje hash nowego i zwraca token jawny
    (do linku). Wywołujący odpowiada za commit."""
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=ttl_hours)).strftime("%Y-%m-%d %H:%M:%S")
    db.execute("UPDATE password_reset_tokens SET used=1 WHERE user_id=? AND used=0", (user_id,))
    db.execute("INSERT INTO password_reset_tokens(user_id,token,expires_at) VALUES(?,?,?)",
               (user_id, hash_reset_token(token), expires_at))
    return token
