"""
Reversible encryption for stored database-connection passwords.

This is deliberately reversible (unlike Django's user password hashing)
because the app needs the real plaintext value back to open a pyodbc
connection later. The Fernet key is derived deterministically from
SECRET_KEY via PBKDF2 so no second secret needs to be provisioned or
rotated separately — note this does mean rotating SECRET_KEY makes
previously-stored passwords undecryptable, same tradeoff Django's own
session/CSRF signing already has.
"""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _fernet():
    key = hashlib.pbkdf2_hmac(
        "sha256", settings.SECRET_KEY.encode(), b"datasources.crypto.v1", 390000, dklen=32
    )
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt(plaintext):
    if not plaintext:
        return ""
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext):
    if not ciphertext:
        return ""
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        return ""
