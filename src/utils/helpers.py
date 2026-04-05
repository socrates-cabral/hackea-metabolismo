"""
helpers.py — Utilidades compartidas de Hackea tu Metabolismo
Soporta SQLite (local) y PostgreSQL (Streamlit Cloud via Supabase)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import logging
import sqlite3
import os
import pandas as pd
from datetime import datetime
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")

BASE_DIR = Path(__file__).parent.parent.parent
_IS_CLOUD = not os.access(BASE_DIR, os.W_OK)
DB_PATH   = Path("/tmp/hackea_metabolismo.db") if _IS_CLOUD else BASE_DIR / os.getenv("DB_PATH", "data/hackea_metabolismo.db")
LOG_DIR   = Path("/tmp/logs") if _IS_CLOUD else BASE_DIR / "logs"


def _get_database_url() -> str | None:
    """Retorna DATABASE_URL desde env o st.secrets."""
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    try:
        import streamlit as st
        return st.secrets.get("DATABASE_URL", None)
    except Exception:
        return None


DATABASE_URL = _get_database_url()


# ── Adaptador PostgreSQL ──────────────────────────────────────

class _PGCursor:
    """Cursor wrapper que imita sqlite3.Row (acceso por nombre de columna)."""
    def __init__(self, cur):
        self._cur = cur

    def fetchone(self):
        row = self._cur.fetchone()
        return dict(row) if row else None

    def fetchall(self):
        return [dict(r) for r in self._cur.fetchall()]

    @property
    def lastrowid(self):
        row = self._cur.fetchone()
        return dict(row).get("id") if row else None


def _encode_pg_url(url: str) -> str:
    """URL-encode la contraseña si contiene caracteres especiales."""
    from urllib.parse import urlparse, quote, urlunparse
    try:
        p = urlparse(url)
        if p.password and any(c in p.password for c in "@#%+!&"):
            encoded = quote(p.password, safe="")
            netloc = f"{p.username}:{encoded}@{p.hostname}"
            if p.port:
                netloc += f":{p.port}"
            return urlunparse(p._replace(netloc=netloc))
    except Exception:
        pass
    return url


class _PGConn:
    """Conexión PostgreSQL que imita la interfaz de sqlite3."""
    def __init__(self, url: str):
        import psycopg2
        from psycopg2.extras import RealDictCursor
        self._conn = psycopg2.connect(_encode_pg_url(url), cursor_factory=RealDictCursor)
        self._conn.autocommit = False
        self._is_pg = True

    def execute(self, sql: str, params=None) -> _PGCursor:
        sql_pg = sql.replace("?", "%s")
        # Agrega RETURNING id automáticamente a INSERTs para obtener el ID
        if (sql_pg.strip().upper().startswith("INSERT")
                and "RETURNING" not in sql_pg.upper()):
            sql_pg = sql_pg.rstrip().rstrip(";") + " RETURNING id"
        cur = self._conn.cursor()
        cur.execute(sql_pg, params or ())
        return _PGCursor(cur)

    def executescript(self, script: str):
        cur = self._conn.cursor()
        for stmt in [s.strip() for s in script.split(";") if s.strip()]:
            cur.execute(stmt)
        self._conn.commit()

    def commit(self):
        self._conn.commit()

    def cursor(self):
        """Expone cursor nativo para pandas.read_sql_query."""
        return self._conn.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, *args):
        if exc_type:
            self._conn.rollback()
        else:
            self._conn.commit()
        self._conn.close()


# ── get_db() — retorna conexión correcta según entorno ───────

def get_db():
    """Retorna conexión PostgreSQL (Cloud) o SQLite (local/fallback)."""
    if DATABASE_URL:
        try:
            return _PGConn(DATABASE_URL)
        except Exception as e:
            print(f"[WARN] PostgreSQL no disponible, fallback a SQLite: {e}", flush=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def read_sql(sql: str, conn, params=None) -> pd.DataFrame:
    """pandas.read_sql_query compatible con sqlite3 y psycopg2."""
    if hasattr(conn, "_is_pg") and conn._is_pg:
        sql_pg = sql.replace("?", "%s")
        return pd.read_sql_query(sql_pg, conn._conn, params=params)
    return pd.read_sql_query(sql, conn, params=params)


# ── Logging ──────────────────────────────────────────────────

def setup_logging(nombre: str) -> logging.Logger:
    LOG_DIR.mkdir(exist_ok=True)
    ts       = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    log_file = LOG_DIR / f"{nombre}_{ts}.log"
    logger   = logging.getLogger(nombre)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
    fh  = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    ch  = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


# ── Utils ─────────────────────────────────────────────────────

def hoy() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def ahora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calcular_edad(fecha_nac: str) -> int:
    nac = datetime.strptime(fecha_nac, "%Y-%m-%d")
    hoy_ = datetime.today()
    return hoy_.year - nac.year - ((hoy_.month, hoy_.day) < (nac.month, nac.day))
