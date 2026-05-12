import copy
import hashlib
import json
import os
import sqlite3
import threading
import time
from contextlib import closing
from typing import Any, Optional

# =========================================================
# BASE DE DATOS DEL SIMULADOR - VERSIÓN OPTIMIZADA
# =========================================================
# Funcionamiento:
# - En local: usa SQLite (simulator.db), como hasta ahora.
# - En Streamlit Cloud: si existe DATABASE_URL en Secrets o variables de entorno,
#   usa PostgreSQL/Supabase automáticamente.
#
# Mejoras de rendimiento:
# - Pool de conexiones para PostgreSQL/Supabase.
# - Caché corta de lecturas frecuentes.
# - Invalidación automática de caché tras escrituras.
# - init_db() solo se ejecuta una vez por sesión/proceso.
#
# En Streamlit Cloud añade en Secrets:
# DATABASE_URL = "postgresql://postgres.xxxxx:TU_PASSWORD@aws-0-eu-west-1.pooler.supabase.com:6543/postgres"
#
# En requirements.txt añade:
# psycopg2-binary
# =========================================================

DB_PATH = os.environ.get("SIM_DB_PATH", os.path.join(os.path.dirname(__file__), "simulator.db"))

# Ajustes de rendimiento.
CACHE_TTL_SECONDS = float(os.environ.get("SIM_DB_CACHE_TTL", "3"))
PG_POOL_MINCONN = int(os.environ.get("SIM_DB_PG_POOL_MINCONN", "1"))
PG_POOL_MAXCONN = int(os.environ.get("SIM_DB_PG_POOL_MAXCONN", "8"))

_DB_INITIALIZED = False
_PG_POOL = None
_PG_POOL_LOCK = threading.Lock()
_CACHE_LOCK = threading.Lock()
_READ_CACHE: dict[str, tuple[float, Any]] = {}


# -------------------------------------------------
# UTILIDADES INTERNAS
# -------------------------------------------------

def _get_database_url() -> Optional[str]:
    """Obtiene la URL de PostgreSQL desde Streamlit Secrets o variables de entorno."""
    try:
        import streamlit as st  # Import opcional para que el archivo siga funcionando fuera de Streamlit.
        if "DATABASE_URL" in st.secrets:
            value = str(st.secrets["DATABASE_URL"]).strip()
            return value if value else None
    except Exception:
        pass

    value = os.environ.get("DATABASE_URL")
    return value.strip() if value else None


def _is_postgres() -> bool:
    url = _get_database_url()
    return bool(url and url.startswith(("postgresql://", "postgres://")))


def _pg_sql(sql: str) -> str:
    """Traduce placeholders SQLite (?) a placeholders psycopg2 (%s)."""
    return sql.replace("?", "%s")


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _cache_get(key: str):
    if CACHE_TTL_SECONDS <= 0:
        return None

    now = time.time()
    with _CACHE_LOCK:
        item = _READ_CACHE.get(key)
        if not item:
            return None

        expires_at, value = item
        if expires_at < now:
            _READ_CACHE.pop(key, None)
            return None

        return copy.deepcopy(value)


def _cache_set(key: str, value: Any):
    if CACHE_TTL_SECONDS <= 0:
        return value

    with _CACHE_LOCK:
        _READ_CACHE[key] = (time.time() + CACHE_TTL_SECONDS, copy.deepcopy(value))

    return value


def _clear_read_cache():
    with _CACHE_LOCK:
        _READ_CACHE.clear()


def _get_pg_pool():
    """Crea o reutiliza un pool de conexiones para Supabase/PostgreSQL."""
    global _PG_POOL

    database_url = _get_database_url()
    if not database_url:
        return None

    with _PG_POOL_LOCK:
        if _PG_POOL is None:
            import psycopg2
            from psycopg2.pool import SimpleConnectionPool
            from psycopg2.extras import RealDictCursor

            _PG_POOL = SimpleConnectionPool(
                PG_POOL_MINCONN,
                PG_POOL_MAXCONN,
                dsn=database_url,
                cursor_factory=RealDictCursor,
            )

        return _PG_POOL


# -------------------------------------------------
# ADAPTADORES POSTGRESQL
# -------------------------------------------------

class PostgresCursor:
    """Adaptador para que psycopg2 se comporte parecido a sqlite3."""

    def __init__(self, cursor):
        self._cursor = cursor
        self.lastrowid = None

    def execute(self, sql: str, params: Any = None):
        sql_clean = sql.strip()
        sql_pg = _pg_sql(sql_clean)

        # En PostgreSQL necesitamos RETURNING para recuperar el id de la partida creada.
        is_insert_games = sql_clean.upper().startswith("INSERT INTO GAMES")
        if is_insert_games and "RETURNING" not in sql_clean.upper():
            sql_pg = sql_pg.rstrip().rstrip(";") + " RETURNING game_id"
            self._cursor.execute(sql_pg, params or ())
            row = self._cursor.fetchone()
            if row is not None:
                self.lastrowid = int(row["game_id"] if isinstance(row, dict) else row[0])
            return self

        self._cursor.execute(sql_pg, params or ())
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def close(self):
        self._cursor.close()

    def __iter__(self):
        return iter(self._cursor)


class PostgresConnection:
    """Adaptador mínimo para mantener la API conn.execute(...) del db.py original."""

    def __init__(self, conn, pool=None):
        self._conn = conn
        self._pool = pool
        self._closed = False

    def cursor(self):
        return PostgresCursor(self._conn.cursor())

    def execute(self, sql: str, params: Any = None):
        cur = self.cursor()
        return cur.execute(sql, params or ())

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        if self._closed:
            return

        self._closed = True
        if self._pool is not None:
            try:
                self._pool.putconn(self._conn)
            except Exception:
                try:
                    self._conn.close()
                except Exception:
                    pass
        else:
            self._conn.close()


def get_conn():
    """Devuelve conexión SQLite local o PostgreSQL/Supabase en producción."""
    database_url = _get_database_url()

    if database_url and database_url.startswith(("postgresql://", "postgres://")):
        pool = _get_pg_pool()
        conn = pool.getconn()
        return PostgresConnection(conn, pool=pool)

    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# -------------------------------------------------
# INICIALIZACIÓN DE BASE DE DATOS
# -------------------------------------------------

def init_db(force: bool = False):
    """Inicializa la base de datos.

    Por rendimiento, solo se ejecuta una vez por proceso salvo que se use force=True.
    """
    global _DB_INITIALIZED

    if _DB_INITIALIZED and not force:
        return

    if _is_postgres():
        _init_postgres_db()
    else:
        _init_sqlite_db()

    _DB_INITIALIZED = True


def _init_sqlite_db():
    with closing(get_conn()) as conn:
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS games (
                game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_name TEXT NOT NULL UNIQUE,
                teams_json TEXT NOT NULL,
                budget_per_team INTEGER NOT NULL,
                round_n INTEGER NOT NULL,
                round_status TEXT NOT NULL,
                engine_state_json TEXT NOT NULL,
                history_json TEXT NOT NULL,
                last_truth_json TEXT,
                last_research_json TEXT,
                last_event_json TEXT,
                team_budgets_json TEXT,
                event_this_round INTEGER NOT NULL DEFAULT 0,
                professor_password_hash TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        game_columns = {row[1] for row in cur.execute("PRAGMA table_info(games)").fetchall()}
        if "team_budgets_json" not in game_columns:
            cur.execute("ALTER TABLE games ADD COLUMN team_budgets_json TEXT")

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS team_access (
                game_id INTEGER NOT NULL,
                team_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                PRIMARY KEY (game_id, team_name),
                FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS decisions (
                game_id INTEGER NOT NULL,
                team_name TEXT NOT NULL,
                round_n INTEGER NOT NULL,
                decision_json TEXT NOT NULL,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed INTEGER NOT NULL DEFAULT 0,
                review_notes TEXT DEFAULT '',
                PRIMARY KEY (game_id, team_name, round_n),
                FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE
            )
            """
        )

        conn.commit()


def _init_postgres_db():
    with closing(get_conn()) as conn:
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS games (
                game_id SERIAL PRIMARY KEY,
                game_name TEXT NOT NULL UNIQUE,
                teams_json TEXT NOT NULL,
                budget_per_team INTEGER NOT NULL,
                round_n INTEGER NOT NULL,
                round_status TEXT NOT NULL,
                engine_state_json TEXT NOT NULL,
                history_json TEXT NOT NULL,
                last_truth_json TEXT,
                last_research_json TEXT,
                last_event_json TEXT,
                team_budgets_json TEXT,
                event_this_round INTEGER NOT NULL DEFAULT 0,
                professor_password_hash TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS team_access (
                game_id INTEGER NOT NULL REFERENCES games(game_id) ON DELETE CASCADE,
                team_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                PRIMARY KEY (game_id, team_name)
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS decisions (
                game_id INTEGER NOT NULL REFERENCES games(game_id) ON DELETE CASCADE,
                team_name TEXT NOT NULL,
                round_n INTEGER NOT NULL,
                decision_json TEXT NOT NULL,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed INTEGER NOT NULL DEFAULT 0,
                review_notes TEXT DEFAULT '',
                PRIMARY KEY (game_id, team_name, round_n)
            )
            """
        )

        # Migración defensiva por si una tabla antigua no tenía esta columna.
        cur.execute(
            """
            ALTER TABLE games
            ADD COLUMN IF NOT EXISTS team_budgets_json TEXT
            """
        )

        # Índices útiles para acelerar lecturas frecuentes.
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_games_updated_at
            ON games (updated_at DESC, game_id DESC)
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_decisions_game_round
            ON decisions (game_id, round_n, team_name)
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_team_access_game_team
            ON team_access (game_id, team_name)
            """
        )

        conn.commit()


# -------------------------------------------------
# CONSULTAS GENERALES DE PARTIDAS
# -------------------------------------------------

def game_exists(game_name: str | None = None) -> bool:
    cache_key = f"game_exists:{game_name!r}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return bool(cached)

    with closing(get_conn()) as conn:
        if game_name:
            row = conn.execute(
                "SELECT 1 FROM games WHERE game_name = ?",
                (game_name,)
            ).fetchone()
        else:
            row = conn.execute("SELECT 1 FROM games LIMIT 1").fetchone()

        result = row is not None
        _cache_set(cache_key, result)
        return result


def list_games():
    cache_key = "list_games"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    with closing(get_conn()) as conn:
        rows = conn.execute(
            """
            SELECT game_id, game_name, round_n, round_status, updated_at
            FROM games
            ORDER BY updated_at DESC, game_id DESC
            """
        ).fetchall()

        result = [
            {
                "game_id": int(row["game_id"]),
                "game_name": row["game_name"],
                "round_n": int(row["round_n"]),
                "round_status": row["round_status"],
                "updated_at": str(row["updated_at"]),
            }
            for row in rows
        ]

        _cache_set(cache_key, result)
        return result


def get_game_by_id(game_id: int):
    cache_key = f"get_game_by_id:{int(game_id)}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    with closing(get_conn()) as conn:
        row = conn.execute(
            """
            SELECT game_id, game_name, round_n, round_status, updated_at
            FROM games
            WHERE game_id = ?
            """,
            (game_id,)
        ).fetchone()

        if row is None:
            _cache_set(cache_key, None)
            return None

        result = {
            "game_id": int(row["game_id"]),
            "game_name": row["game_name"],
            "round_n": int(row["round_n"]),
            "round_status": row["round_status"],
            "updated_at": str(row["updated_at"]),
        }

        _cache_set(cache_key, result)
        return result


def get_game_by_name(game_name: str):
    cache_key = f"get_game_by_name:{game_name!r}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    with closing(get_conn()) as conn:
        row = conn.execute(
            """
            SELECT game_id, game_name, round_n, round_status, updated_at
            FROM games
            WHERE game_name = ?
            """,
            (game_name,)
        ).fetchone()

        if row is None:
            _cache_set(cache_key, None)
            return None

        result = {
            "game_id": int(row["game_id"]),
            "game_name": row["game_name"],
            "round_n": int(row["round_n"]),
            "round_status": row["round_status"],
            "updated_at": str(row["updated_at"]),
        }

        _cache_set(cache_key, result)
        return result


def get_latest_game_id():
    cache_key = "get_latest_game_id"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    with closing(get_conn()) as conn:
        row = conn.execute(
            """
            SELECT game_id
            FROM games
            ORDER BY updated_at DESC, game_id DESC
            LIMIT 1
            """
        ).fetchone()

        result = int(row["game_id"]) if row else None
        _cache_set(cache_key, result)
        return result


# -------------------------------------------------
# CREAR / DUPLICAR / RENOMBRAR / BORRAR PARTIDAS
# -------------------------------------------------

def create_game(
    *,
    game_name,
    teams,
    team_passwords,
    budget_per_team,
    round_n,
    round_status,
    engine_state,
    history,
    last_truth,
    last_research,
    last_event,
    team_budgets=None,
    event_this_round=False,
    professor_password="admin123",
):
    with closing(get_conn()) as conn:
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO games (
                game_name, teams_json, budget_per_team, round_n, round_status,
                engine_state_json, history_json, last_truth_json, last_research_json,
                last_event_json, team_budgets_json, event_this_round, professor_password_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                game_name,
                json.dumps(teams, ensure_ascii=False),
                int(budget_per_team),
                int(round_n),
                round_status,
                json.dumps(engine_state, ensure_ascii=False),
                json.dumps(history or [], ensure_ascii=False),
                json.dumps(last_truth, ensure_ascii=False) if last_truth is not None else None,
                json.dumps(last_research, ensure_ascii=False) if last_research is not None else None,
                json.dumps(last_event, ensure_ascii=False) if last_event is not None else None,
                json.dumps(team_budgets or {team: int(budget_per_team) for team in teams}, ensure_ascii=False),
                int(bool(event_this_round)),
                _hash_password(professor_password),
            )
        )

        game_id = cur.lastrowid

        for team in teams:
            pwd = team_passwords.get(team, "1234")
            cur.execute(
                """
                INSERT INTO team_access (game_id, team_name, password_hash)
                VALUES (?, ?, ?)
                """,
                (game_id, team, _hash_password(pwd))
            )

        conn.commit()

    _clear_read_cache()
    return int(game_id)


def create_or_replace_game(
    *,
    game_name,
    teams,
    team_passwords,
    budget_per_team,
    round_n,
    round_status,
    engine_state,
    history,
    last_truth,
    last_research,
    last_event,
    team_budgets=None,
    event_this_round=False,
    professor_password="admin123",
):
    existing = get_game_by_name(game_name)
    if existing:
        delete_game(existing["game_id"])

    return create_game(
        game_name=game_name,
        teams=teams,
        team_passwords=team_passwords,
        budget_per_team=budget_per_team,
        round_n=round_n,
        round_status=round_status,
        engine_state=engine_state,
        history=history,
        last_truth=last_truth,
        last_research=last_research,
        last_event=last_event,
        team_budgets=team_budgets,
        event_this_round=event_this_round,
        professor_password=professor_password,
    )


def rename_game(game_id: int, new_game_name: str):
    with closing(get_conn()) as conn:
        conn.execute(
            """
            UPDATE games
            SET game_name = ?, updated_at = CURRENT_TIMESTAMP
            WHERE game_id = ?
            """,
            (new_game_name, game_id)
        )
        conn.commit()

    _clear_read_cache()


def delete_game(game_id: int):
    with closing(get_conn()) as conn:
        # Aunque existe ON DELETE CASCADE, se mantiene el borrado explícito por compatibilidad.
        conn.execute("DELETE FROM decisions WHERE game_id = ?", (game_id,))
        conn.execute("DELETE FROM team_access WHERE game_id = ?", (game_id,))
        conn.execute("DELETE FROM games WHERE game_id = ?", (game_id,))
        conn.commit()

    _clear_read_cache()


def duplicate_game(source_game_id: int, new_game_name: str):
    state = load_game_state(source_game_id)
    if state is None:
        return None

    with closing(get_conn()) as conn:
        team_rows = conn.execute(
            """
            SELECT team_name
            FROM team_access
            WHERE game_id = ?
            ORDER BY team_name
            """,
            (source_game_id,)
        ).fetchall()

        team_names = [row["team_name"] for row in team_rows]

    # En una duplicación no conocemos las claves originales en texto plano.
    # Dejamos una clave inicial común por defecto para todos los equipos.
    team_passwords = {team: "1234" for team in team_names}

    new_game_id = create_game(
        game_name=new_game_name,
        teams=state["teams"],
        team_passwords=team_passwords,
        budget_per_team=state["budget_per_team"],
        round_n=state["round_n"],
        round_status=state["round_status"],
        engine_state=state["engine_state"],
        history=state["history"],
        last_truth=state["last_truth"],
        last_research=state["last_research"],
        last_event=state["last_event"],
        team_budgets=state.get("team_budgets"),
        event_this_round=state["event_this_round"],
        professor_password="admin123",
    )

    with closing(get_conn()) as conn:
        decision_rows = conn.execute(
            """
            SELECT team_name, round_n, decision_json, submitted_at, reviewed, review_notes
            FROM decisions
            WHERE game_id = ?
            """,
            (source_game_id,)
        ).fetchall()

        for row in decision_rows:
            conn.execute(
                """
                INSERT INTO decisions (
                    game_id, team_name, round_n, decision_json,
                    submitted_at, reviewed, review_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_game_id,
                    row["team_name"],
                    int(row["round_n"]),
                    row["decision_json"],
                    row["submitted_at"],
                    int(row["reviewed"]),
                    row["review_notes"] or "",
                )
            )

        conn.commit()

    _clear_read_cache()
    return new_game_id


# -------------------------------------------------
# CARGA Y ACTUALIZACIÓN DEL ESTADO
# -------------------------------------------------

def load_game_state(game_id: int):
    cache_key = f"load_game_state:{int(game_id)}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    with closing(get_conn()) as conn:
        row = conn.execute(
            "SELECT * FROM games WHERE game_id = ?",
            (game_id,)
        ).fetchone()

        if row is None:
            _cache_set(cache_key, None)
            return None

        teams = json.loads(row["teams_json"])
        result = {
            "game_id": int(row["game_id"]),
            "game_name": row["game_name"],
            "teams": teams,
            "budget_per_team": int(row["budget_per_team"]),
            "round_n": int(row["round_n"]),
            "round_status": row["round_status"],
            "engine_state": json.loads(row["engine_state_json"]),
            "history": json.loads(row["history_json"] or "[]"),
            "last_truth": json.loads(row["last_truth_json"]) if row["last_truth_json"] else None,
            "last_research": json.loads(row["last_research_json"]) if row["last_research_json"] else None,
            "last_event": json.loads(row["last_event_json"]) if row["last_event_json"] else None,
            "team_budgets": json.loads(row["team_budgets_json"]) if row["team_budgets_json"] else {
                team: int(row["budget_per_team"]) for team in teams
            },
            "event_this_round": bool(row["event_this_round"]),
            "updated_at": str(row["updated_at"]),
        }

        _cache_set(cache_key, result)
        return result


def update_game_state(game_id: int, **fields):
    if not fields:
        return

    mapped = {}
    for key, value in fields.items():
        if key == "teams":
            mapped["teams_json"] = json.dumps(value, ensure_ascii=False)
        elif key == "engine_state":
            mapped["engine_state_json"] = json.dumps(value, ensure_ascii=False)
        elif key == "history":
            mapped["history_json"] = json.dumps(value, ensure_ascii=False)
        elif key == "last_truth":
            mapped["last_truth_json"] = json.dumps(value, ensure_ascii=False) if value is not None else None
        elif key == "last_research":
            mapped["last_research_json"] = json.dumps(value, ensure_ascii=False) if value is not None else None
        elif key == "last_event":
            mapped["last_event_json"] = json.dumps(value, ensure_ascii=False) if value is not None else None
        elif key == "team_budgets":
            mapped["team_budgets_json"] = json.dumps(value, ensure_ascii=False) if value is not None else None
        elif key == "event_this_round":
            mapped["event_this_round"] = int(bool(value))
        else:
            mapped[key] = value

    columns = ", ".join(f"{k} = ?" for k in mapped.keys()) + ", updated_at = CURRENT_TIMESTAMP"
    values = list(mapped.values())
    values.append(game_id)

    with closing(get_conn()) as conn:
        conn.execute(f"UPDATE games SET {columns} WHERE game_id = ?", values)
        conn.commit()

    _clear_read_cache()


# -------------------------------------------------
# CLAVES
# -------------------------------------------------

def set_professor_password(game_id: int, password: str):
    with closing(get_conn()) as conn:
        conn.execute(
            """
            UPDATE games
            SET professor_password_hash = ?, updated_at = CURRENT_TIMESTAMP
            WHERE game_id = ?
            """,
            (_hash_password(password), game_id)
        )
        conn.commit()

    _clear_read_cache()


def verify_professor_password(game_id: int, password: str) -> bool:
    # No se cachea por seguridad: evita resultados raros justo tras cambiar clave.
    with closing(get_conn()) as conn:
        row = conn.execute(
            "SELECT professor_password_hash FROM games WHERE game_id = ?",
            (game_id,)
        ).fetchone()

        if row is None:
            return False

        return row["professor_password_hash"] == _hash_password(password)


def verify_team_password(game_id: int, team_name: str, password: str) -> bool:
    # No se cachea por seguridad: evita resultados raros justo tras cambiar clave.
    with closing(get_conn()) as conn:
        row = conn.execute(
            """
            SELECT password_hash
            FROM team_access
            WHERE game_id = ? AND team_name = ?
            """,
            (game_id, team_name)
        ).fetchone()

        if row is None:
            return False

        return row["password_hash"] == _hash_password(password)


def update_team_password(game_id: int, team_name: str, password: str):
    with closing(get_conn()) as conn:
        conn.execute(
            """
            UPDATE team_access
            SET password_hash = ?
            WHERE game_id = ? AND team_name = ?
            """,
            (_hash_password(password), game_id, team_name)
        )
        conn.commit()

    _clear_read_cache()


def list_team_passwords_masked(game_id: int):
    cache_key = f"list_team_passwords_masked:{int(game_id)}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    with closing(get_conn()) as conn:
        rows = conn.execute(
            """
            SELECT team_name
            FROM team_access
            WHERE game_id = ?
            ORDER BY team_name
            """,
            (game_id,)
        ).fetchall()

        result = [row["team_name"] for row in rows]
        _cache_set(cache_key, result)
        return result


# -------------------------------------------------
# DECISIONES
# -------------------------------------------------

def upsert_decision(game_id: int, team_name: str, round_n: int, decision: dict):
    with closing(get_conn()) as conn:
        conn.execute(
            """
            INSERT INTO decisions (game_id, team_name, round_n, decision_json, reviewed, review_notes)
            VALUES (?, ?, ?, ?, 0, '')
            ON CONFLICT(game_id, team_name, round_n) DO UPDATE SET
                decision_json = excluded.decision_json,
                submitted_at = CURRENT_TIMESTAMP,
                reviewed = 0,
                review_notes = ''
            """,
            (game_id, team_name, round_n, json.dumps(decision, ensure_ascii=False))
        )
        conn.commit()

    _clear_read_cache()


def get_decision(game_id: int, team_name: str, round_n: int):
    cache_key = f"get_decision:{int(game_id)}:{team_name!r}:{int(round_n)}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    with closing(get_conn()) as conn:
        row = conn.execute(
            """
            SELECT *
            FROM decisions
            WHERE game_id = ? AND team_name = ? AND round_n = ?
            """,
            (game_id, team_name, round_n)
        ).fetchone()

        if row is None:
            _cache_set(cache_key, None)
            return None

        result = {
            "game_id": int(row["game_id"]),
            "team_name": row["team_name"],
            "round_n": int(row["round_n"]),
            "decision": json.loads(row["decision_json"]),
            "reviewed": bool(row["reviewed"]),
            "review_notes": row["review_notes"] or "",
            "submitted_at": str(row["submitted_at"]),
        }

        _cache_set(cache_key, result)
        return result


def get_all_decisions(game_id: int, round_n: int):
    cache_key = f"get_all_decisions:{int(game_id)}:{int(round_n)}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    with closing(get_conn()) as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM decisions
            WHERE game_id = ? AND round_n = ?
            ORDER BY team_name
            """,
            (game_id, round_n)
        ).fetchall()

        out = {}
        for row in rows:
            out[row["team_name"]] = {
                "decision": json.loads(row["decision_json"]),
                "reviewed": bool(row["reviewed"]),
                "review_notes": row["review_notes"] or "",
                "submitted_at": str(row["submitted_at"]),
            }

        _cache_set(cache_key, out)
        return out


def set_review_status(game_id: int, team_name: str, round_n: int, reviewed: bool, review_notes: str = ""):
    with closing(get_conn()) as conn:
        conn.execute(
            """
            UPDATE decisions
            SET reviewed = ?, review_notes = ?
            WHERE game_id = ? AND team_name = ? AND round_n = ?
            """,
            (int(bool(reviewed)), review_notes, game_id, team_name, round_n)
        )
        conn.commit()

    _clear_read_cache()


def delete_decisions_for_round(game_id: int, round_n: int):
    with closing(get_conn()) as conn:
        conn.execute(
            """
            DELETE FROM decisions
            WHERE game_id = ? AND round_n = ?
            """,
            (game_id, round_n)
        )
        conn.commit()

    _clear_read_cache()
