"""US-014: ręczny przegląd RODO — to samo, co aplikacja robi raz na dobę w tle.

Usuwa dane osobowe starsze niż 12 miesięcy (audit_log, api_usage, api_rate_events) i anonimizuje
konta nieaktywne dłużej niż 30 dni. Idempotentny.

    python tools/privacy_maintenance.py

Baza wskazana jak dla aplikacji: DATABASE_URL (PostgreSQL) albo SQLITE_PATH.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.privacy import run_maintenance  # noqa: E402
from db import get_db  # noqa: E402

if __name__ == "__main__":
    print(json.dumps(run_maintenance(get_db), ensure_ascii=False))
