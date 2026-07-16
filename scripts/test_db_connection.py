import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL is not set in .env")
    exit(1)

# Ensure psycopg2 is used if postgresql:// is the scheme
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

print(f"Connecting to: {DATABASE_URL.split('@')[-1]}") # Print host info safely

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        if result == 1:
            print("✅ Supabase connection is solid (SELECT 1 succeeded).")
        else:
            print(f"❌ Connection worked but returned unexpected result: {result}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
