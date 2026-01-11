import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# --------------------------------------------------
# Explicitly load .env from project root
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[3]
# parents[3] = backend/

load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
print("FASTAPI DATABASE_URL =", DATABASE_URL)

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,     # kills dead connections
    pool_recycle=1800,      # refresh every 30 mins
    echo=False
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)
