import hashlib
import os


ROUNDS = 256


def get_pepper() -> str:
    pepper = os.environ.get("PASSWORD_PEPPER")
    if not pepper:
        raise RuntimeError("PASSWORD_PEPPER is not configured")
    return pepper


def encrypt_password(password: str) -> str:
    value = (password + get_pepper()).encode("utf-8")
    for _ in range(ROUNDS):
        value = hashlib.sha256(value).hexdigest().encode("utf-8")
    return value.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return encrypt_password(password) == hashed
