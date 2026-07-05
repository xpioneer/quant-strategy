from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config.settings import get_settings

settings = get_settings()

if settings.database_url.startswith("sqlite"):
    engine = create_engine(settings.database_url, connect_args={"check_same_thread": False}, future=True)
else:
    engine = create_engine(settings.database_url, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ensure_kline_columns():
    inspector = inspect(engine)
    if "klines" not in inspector.get_table_names():
        return

    existing = {col['name'] for col in inspector.get_columns('klines')}
    alters = []
    if 'amplitude' not in existing:
        alters.append('ALTER TABLE klines ADD COLUMN amplitude FLOAT')
    if 'pct_change' not in existing:
        alters.append('ALTER TABLE klines ADD COLUMN pct_change FLOAT')
    if 'change' not in existing:
        alters.append('ALTER TABLE klines ADD COLUMN change FLOAT')
    if 'turnover_rate' not in existing:
        alters.append('ALTER TABLE klines ADD COLUMN turnover_rate FLOAT')

    if alters:
        with engine.begin() as conn:
            for stmt in alters:
                conn.execute(text(stmt))
