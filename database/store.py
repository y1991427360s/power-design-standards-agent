import sqlite3
from contextlib import contextmanager
from config.settings import DB

@contextmanager
def connect():
    db = sqlite3.connect(DB, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    with connect() as db:
        db.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS documents (
          document_id TEXT PRIMARY KEY, filename TEXT NOT NULL, standard_name TEXT NOT NULL,
          standard_code TEXT DEFAULT '', version TEXT DEFAULT '', publication_date TEXT DEFAULT '',
          effective_date TEXT DEFAULT '', source_type TEXT NOT NULL, standard_type TEXT DEFAULT '',
          category TEXT DEFAULT '', status TEXT DEFAULT '解析中', source_file TEXT NOT NULL,
          created_at TEXT NOT NULL, is_demo INTEGER DEFAULT 0, warning TEXT DEFAULT '',
          lifecycle TEXT DEFAULT '现行', supersedes TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS clauses (
          id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
          chapter TEXT, section TEXT, clause TEXT, title TEXT, text TEXT NOT NULL,
          page INTEGER NOT NULL, page_end INTEGER NOT NULL, page_kind TEXT NOT NULL,
          parse_quality TEXT NOT NULL, vector TEXT NOT NULL, embedding_id TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS clause_doc ON clauses(document_id);
        CREATE TABLE IF NOT EXISTS rules (
          id TEXT PRIMARY KEY, title TEXT NOT NULL, category TEXT, condition TEXT, rule TEXT NOT NULL,
          exceptions TEXT, source TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS conversations (
          id TEXT PRIMARY KEY, title TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS messages (
          id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id TEXT REFERENCES conversations(id) ON DELETE CASCADE,
          question TEXT NOT NULL, answer TEXT NOT NULL, created_at TEXT NOT NULL);
        ''')

def all_clauses():
    with connect() as db:
        return [dict(r) for r in db.execute('''SELECT c.*, d.* FROM clauses c JOIN documents d
          ON c.document_id=d.document_id WHERE d.status='已就绪' AND d.lifecycle='现行' ORDER BY d.created_at,c.page,c.rowid''')]
