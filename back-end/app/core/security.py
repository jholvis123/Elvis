"""
Utilidades de seguridad: hashing de contraseñas.
"""

from passlib.context import CryptContext

# Contexto para hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Genera un hash seguro de la contraseña."""
    # bcrypt tiene límite de 72 bytes
    # Asegurarse de truncar correctamente en límites de caracteres UTF-8
    if len(password.encode('utf-8')) > 72:
        # Truncar byte a byte hasta 72
        truncated = password.encode('utf-8')[:72]
        # Decodificar ignorando bytes incompletos al final
        password = truncated.decode('utf-8', errors='ignore')
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica que la contraseña coincida con el hash."""
    # Aplicar mismo truncamiento para verificación
    if len(plain_password.encode('utf-8')) > 72:
        truncated = plain_password.encode('utf-8')[:72]
        plain_password = truncated.decode('utf-8', errors='ignore')
    return pwd_context.verify(plain_password, hashed_password)
