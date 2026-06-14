"""Adaptador PostgreSQL para telegram_bot — lee alertas, gestiona suscripciones."""
import logging
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras

logger = logging.getLogger("telegram_bot.postgres")


class PostgresAdapter:
    def __init__(self, db_url: str):
        self._url = db_url
        self._conn = None

    def connect(self):
        self._conn = psycopg2.connect(self._url)
        self._conn.autocommit = False

    def close(self):
        if self._conn:
            self._conn.close()

    def ping(self) -> bool:
        try:
            with self._conn.cursor() as cur:
                cur.execute("SELECT 1")
            return True
        except Exception:
            return False

    def reconnect(self):
        try:
            self.close()
        except Exception:
            pass
        self.connect()

    def get_pending_telegram_alerts(self) -> list[dict]:
        """Alertas activas aún no enviadas por Telegram."""
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT sa.id, sa.probability, sa.alert_level, sa.generated_at, sa.model_version,
                       ws.name AS station_name, ws.department, ws.code AS station_code
                FROM storm_alerts sa
                JOIN weather_stations ws ON ws.id = sa.station_id
                WHERE sa.is_active = TRUE
                  AND sa.telegram_notified_at IS NULL
                ORDER BY sa.generated_at DESC
                """
            )
            return [dict(r) for r in cur.fetchall()]

    def mark_telegram_notified(self, alert_ids: list[int]):
        if not alert_ids:
            return
        with self._conn.cursor() as cur:
            cur.execute(
                "UPDATE storm_alerts SET telegram_notified_at = NOW() WHERE id = ANY(%s)",
                (alert_ids,),
            )
        self._conn.commit()

    def get_subscribers_for_alert(self, department: str, alert_level: int) -> list[dict]:
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT chat_id, username
                FROM telegram_subscriptions
                WHERE is_active = TRUE
                  AND min_level <= %s
                  AND (department = '' OR department ILIKE %s)
                """,
                (alert_level, department),
            )
            return [dict(r) for r in cur.fetchall()]

    def upsert_subscription(self, chat_id: int, username: str, department: str = "", min_level: int = 2):
        with self._conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO telegram_subscriptions (chat_id, username, department, min_level, is_active, created_at)
                VALUES (%s, %s, %s, %s, TRUE, NOW())
                ON CONFLICT (chat_id) DO UPDATE
                  SET username = EXCLUDED.username,
                      department = EXCLUDED.department,
                      min_level = EXCLUDED.min_level,
                      is_active = TRUE
                """,
                (chat_id, username, department, min_level),
            )
        self._conn.commit()

    def deactivate_subscription(self, chat_id: int):
        with self._conn.cursor() as cur:
            cur.execute(
                "UPDATE telegram_subscriptions SET is_active = FALSE WHERE chat_id = %s",
                (chat_id,),
            )
        self._conn.commit()

    def get_subscription(self, chat_id: int) -> dict | None:
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM telegram_subscriptions WHERE chat_id = %s",
                (chat_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def get_active_alerts_summary(self) -> list[dict]:
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT sa.alert_level, sa.probability, ws.name AS station_name, ws.department
                FROM storm_alerts sa
                JOIN weather_stations ws ON ws.id = sa.station_id
                WHERE sa.is_active = TRUE
                ORDER BY sa.alert_level DESC, sa.probability DESC
                LIMIT 10
                """
            )
            return [dict(r) for r in cur.fetchall()]
