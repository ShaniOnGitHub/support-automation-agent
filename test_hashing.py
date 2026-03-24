from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

try:
    hash = pwd_context.hash("password".encode("utf-8"))
    print(f"Hash: {hash}")
    verify = pwd_context.verify("password", hash)
    print(f"Verify: {verify}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
