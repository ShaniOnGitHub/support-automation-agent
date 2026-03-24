try:
    import passlib
    print("passlib OK")
    import jose
    print("jose OK")
    import multipart
    print("multipart OK")
    import pydantic
    from pydantic import EmailStr
    print("pydantic OK")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
