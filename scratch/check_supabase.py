from sqlalchemy import create_engine, text

db_url = "postgresql://postgres.pzfoturzvospoodpivcz:Roshaan123%40@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"
engine = create_engine(db_url)

try:
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
        print("pgvector extension created or verified successfully!")
except Exception as e:
    print("Error enabling pgvector extension:", str(e))
