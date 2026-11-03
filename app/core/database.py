from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Auto-migrate SQLite missing columns if table already existed
    if "sqlite" in settings.DATABASE_URL:
        from sqlalchemy import text
        with engine.connect() as conn:
            try:
                result = conn.execute(text("PRAGMA table_info(episodes)"))
                existing_cols = {row[1] for row in result.fetchall()}
                
                if "dialogue_style" not in existing_cols:
                    conn.execute(text("ALTER TABLE episodes ADD COLUMN dialogue_style VARCHAR(50) DEFAULT 'code_mixed'"))
                if "sources" not in existing_cols:
                    conn.execute(text("ALTER TABLE episodes ADD COLUMN sources TEXT DEFAULT '[]'"))
                conn.commit()
            except Exception as e:
                # Table might not exist yet or already updated
                pass

