"""
Utilidades de seguridad: hashing de contraseñas.
"""

import bcrypt


def _password_bytes(password: str) -> bytes:
    """bcrypt limita a 72 bytes; truncar en límite UTF-8 seguro."""
    raw = password.encode("utf-8")
    if len(raw) <= 72:
        return raw
    return raw[:72]


def get_password_hash(password: str) -> str:
    """Genera un hash seguro de la contraseña."""
    # bcrypt directo: evita ValueError de passlib 1.7.4 detect_wrap_bug
    # con bcrypt>=4.1 incluso para passwords cortas.
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt()).decode("ascii")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica que la contraseña coincida con el hash."""
    try:
        return bcrypt.checkpw(
            _password_bytes(plain_password),
            hashed_password.encode("ascii"),
        )
    except (ValueError, TypeError):
        return False
