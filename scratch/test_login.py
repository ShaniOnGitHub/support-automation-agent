from sqlalchemy import create_engine, text
from app.core import security

db_url = "postgresql://postgres.pzfoturzvospoodpivcz:Roshaan123%40@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"
engine = create_engine(db_url)

try:
    with engine.connect() as conn:
        res = conn.execute(text("SELECT email, hashed_password FROM users"))
        for row in res:
            email = row[0]
            hashed = row[1]
            print("Email:", email)
            # Test some possible passwords
            for pwd in ["Roshaan123@", "Roshaan123!", "Roshaan123", "password123"]:
                matches = security.verify_password(pwd, hashed)
                print(f"  Password '{pwd}' matches: {matches}")
except Exception as e:
    print("Error:", str(e))
