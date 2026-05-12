import json
import os
import sqlite3
import hashlib
from contextlib import closing
from typing import Any, Optional

# =========================================================
# BASE DE DATOS DEL SIMULADOR
# =========================================================
# Funcionamiento:
# - En local: usa SQLite (simulator.db), como hasta ahora.
# - En Streamlit Cloud: si existe DATABASE_URL en Secrets o variables de entorno,
#   usa PostgreSQL/Supabase automáticamente.
#
# En Streamlit Cloud añade en Secrets:
# DATABASE_URL = "postgresql://postgres:TU_PASSWORD@db.xxxxx.supabase.co:5432/postgres"
#
# En requirements.txt añade:
# psycopg2-binary
# =========================================================

DB_PATH = os.environ.get("SIM_DB_PATH", os.path.join(os.path.dirname(__file__), "simulator.db"))


def _get_database_url() -> Optional[str]:
    """Obtiene la URL de PostgreSQL desde Streamlit Secrets o variables de entorno."""
    try:
        import streamlit as st  # Import opcional para que el archivo siga funcionando fuera de Streamlit.
        if "DATABASE_URL" in st.secrets:
            return str(st.secrets["DATABASE_URL"]).strip()
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


class PostgresCursor:
    """Pequeño adaptador para que psycopg2 se comporte parecido a sqlite3."""

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

    def __init__(self, conn):
        self._conn = conn

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
        self._conn.close()



def get_conn():
    """Devuelve conexión SQLite local o PostgreSQL/Supabase en producción."""
    database_url = _get_database_url()

    if database_url and database_url.startswith(("postgresql://", "postgres://")):
        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        return PostgresConnection(conn)

    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# -------------------------------------------------
# INICIALIZACIÓN DE BASE DE DATOS
# -------------------------------------------------

def init_db():
    if _is_postgres():
        _init_postgres_db()
    else:
        _init_sqlite_db()


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

        conn.commit()


# -------------------------------------------------
# CONSULTAS GENERALES DE PARTIDAS
# -------------------------------------------------

def game_exists(game_name: str | None = None) -> bool:
    with closing(get_conn()) as conn:
        if game_name:
            row = conn.execute(
                "SELECT 1 FROM games WHERE game_name = ?",
                (game_name,)
            ).fetchone()
        else:
            row = conn.execute("SELECT 1 FROM games LIMIT 1").fetchone()
        return row is not None


def list_games():
    with closing(get_conn()) as conn:
        rows = conn.execute(
            """
            SELECT game_id, game_name, round_n, round_status, updated_at
            FROM games
            ORDER BY updated_at DESC, game_id DESC
            """
        ).fetchall()

        return [
            {
                "game_id": int(row["game_id"]),
                "game_name": row["game_name"],
                "round_n": int(row["round_n"]),
                "round_status": row["round_status"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]


def get_game_by_id(game_id: int):
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
            return None

        return {
            "game_id": int(row["game_id"]),
            "game_name": row["game_name"],
            "round_n": int(row["round_n"]),
            "round_status": row["round_status"],
            "updated_at": row["updated_at"],
        }


def get_game_by_name(game_name: str):
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
            return None

        return {
            "game_id": int(row["game_id"]),
            "game_name": row["game_name"],
            "round_n": int(row["round_n"]),
            "round_status": row["round_status"],
            "updated_at": row["updated_at"],
        }


def get_latest_game_id():
    with closing(get_conn()) as conn:
        row = conn.execute(
            """
            SELECT game_id
            FROM games
            ORDER BY updated_at DESC, game_id DESC
            LIMIT 1
            """
        ).fetchone()
        return int(row["game_id"]) if row else None


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


def delete_game(game_id: int):
    with closing(get_conn()) as conn:
        # Aunque existe ON DELETE CASCADE, se mantiene el borrado explícito por compatibilidad.
        conn.execute("DELETE FROM decisions WHERE game_id = ?", (game_id,))
        conn.execute("DELETE FROM team_access WHERE game_id = ?", (game_id,))
        conn.execute("DELETE FROM games WHERE game_id = ?", (game_id,))
        conn.commit()


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

    return new_game_id


# -------------------------------------------------
# CARGA Y ACTUALIZACIÓN DEL ESTADO
# -------------------------------------------------

def load_game_state(game_id: int):
    with closing(get_conn()) as conn:
        row = conn.execute(
            "SELECT * FROM games WHERE game_id = ?",
            (game_id,)
        ).fetchone()

        if row is None:
            return None

        teams = json.loads(row["teams_json"])
        return {
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
            "updated_at": row["updated_at"],
        }


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


def verify_professor_password(game_id: int, password: str) -> bool:
    with closing(get_conn()) as conn:
        row = conn.execute(
            "SELECT professor_password_hash FROM games WHERE game_id = ?",
            (game_id,)
        ).fetchone()

        if row is None:
            return False

        return row["professor_password_hash"] == _hash_password(password)


def verify_team_password(game_id: int, team_name: str, password: str) -> bool:
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


def list_team_passwords_masked(game_id: int):
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

        return [row["team_name"] for row in rows]


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


def get_decision(game_id: int, team_name: str, round_n: int):
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
            return None

        return {
            "game_id": int(row["game_id"]),
            "team_name": row["team_name"],
            "round_n": int(row["round_n"]),
            "decision": json.loads(row["decision_json"]),
            "reviewed": bool(row["reviewed"]),
            "review_notes": row["review_notes"] or "",
            "submitted_at": row["submitted_at"],
        }


def get_all_decisions(game_id: int, round_n: int):
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
                "submitted_at": row["submitted_at"],
            }
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
