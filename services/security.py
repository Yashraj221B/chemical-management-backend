import bcrypt


def _to_bytes(value):
    if isinstance(value, bytes):
        return value
    return value.encode("utf-8")


def hash_password(password):
    password_bytes = _to_bytes(password)
    if len(password_bytes) > 72:
        raise ValueError("Password cannot be longer than 72 bytes")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password, hashed_password):
    try:
        return bcrypt.checkpw(_to_bytes(plain_password), _to_bytes(hashed_password))
    except ValueError:
        return False
