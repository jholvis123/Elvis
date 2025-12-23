"""
Script para crear un usuario administrador inicial en la base de datos.
Ejecuta este script una sola vez para crear el admin.

Uso:
    # Con variables de entorno (recomendado en producción):
    ADMIN_EMAIL=tu@email.com ADMIN_USERNAME=admin ADMIN_PASSWORD=tu_password_seguro python create_admin.py
    
    # O configura en tu archivo .env:
    ADMIN_EMAIL=tu@email.com
    ADMIN_USERNAME=admin
    ADMIN_PASSWORD=tu_password_seguro
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.infrastructure.persistence.models.user_model import UserModel
from app.core.security import get_password_hash
import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:@localhost/portafolio_db")

# Crear engine y sesión
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def create_admin_user():
    """Crea un usuario administrador si no existe."""
    db = SessionLocal()
    
    try:
        # Credenciales del admin desde variables de entorno (seguro)
        ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
        ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
        ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
        
        # Validar que las credenciales estén configuradas
        if not all([ADMIN_EMAIL, ADMIN_USERNAME, ADMIN_PASSWORD]):
            print("❌ Error: Debes configurar las variables de entorno:")
            print("   ADMIN_EMAIL, ADMIN_USERNAME, ADMIN_PASSWORD")
            print("\n   Ejemplo:")
            print('   ADMIN_EMAIL=admin@tudominio.com ADMIN_USERNAME=admin ADMIN_PASSWORD=tu_password python create_admin.py')
            print("\n   O agrégalas a tu archivo .env")
            sys.exit(1)
        
        # Validar longitud mínima de password
        if len(ADMIN_PASSWORD) < 8:
            print("❌ Error: La contraseña debe tener al menos 8 caracteres")
            sys.exit(1)
        
        # Truncar password a 72 caracteres (límite de bcrypt)
        password_to_hash = ADMIN_PASSWORD[:72]
        
        # Verificar si ya existe
        existing_admin = db.query(UserModel).filter(UserModel.email == ADMIN_EMAIL).first()
        
        if existing_admin:
            print(f"⚠️  El usuario admin ya existe: {ADMIN_EMAIL}")
            print(f"   Username: {existing_admin.username}")
            print(f"   Is Admin: {existing_admin.is_admin}")
            return
        
        # Crear nuevo admin
        hashed_password = get_password_hash(password_to_hash)
        
        admin_user = UserModel(
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            hashed_password=hashed_password,
            is_admin=True,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ Usuario administrador creado exitosamente!")
        print(f"   Email: {ADMIN_EMAIL}")
        print(f"   Username: {ADMIN_USERNAME}")
        print(f"   ID: {admin_user.id}")
        print("\n⚠️  Guarda tus credenciales en un lugar seguro.")
        
    except Exception as e:
        print(f"❌ Error al crear usuario admin: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 Creando usuario administrador...")
    create_admin_user()
