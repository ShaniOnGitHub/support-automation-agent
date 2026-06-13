from sqlalchemy import create_engine, text

db_url = "postgresql://postgres.pzfoturzvospoodpivcz:Roshaan123%40@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"
engine = create_engine(db_url)

try:
    with engine.connect() as conn:
        res = conn.execute(text("SELECT email, hashed_password FROM users"))
        for row in res:
            print("Email:", row[0])
except Exception as e:
    print("Error:", str(e))
