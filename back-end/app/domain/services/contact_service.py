"""
Servicio de dominio para Contact.
Contiene la lógica de negocio para mensajes de contacto.
"""

from typing import Optional, Dict, List
from uuid import UUID

from ..entities.contact import Contact, ProjectType
from ..repositories.contact_repo import ContactRepository


class ContactService:
    """Servicio de dominio para lógica de mensajes de contacto."""
    
    # Límites de validación
    MIN_NAME_LENGTH = 2
    MAX_NAME_LENGTH = 100
    MIN_MESSAGE_LENGTH = 10
    MAX_MESSAGE_LENGTH = 2000
    
    def __init__(self, contact_repository: ContactRepository):
        self.contact_repository = contact_repository
    
    def validate_contact_data(
        self,
        name: str,
        email: str,
        project_type: str,
        message: str,
    ) -> Dict[str, str]:
        """
        Valida los datos del formulario de contacto.
        
        Returns:
            Dict con errores (vacío si no hay errores)
        """
        errors = {}
        
        # Validar nombre
        if not name or len(name.strip()) < self.MIN_NAME_LENGTH:
            errors["name"] = f"El nombre debe tener al menos {self.MIN_NAME_LENGTH} caracteres"
        elif len(name) > self.MAX_NAME_LENGTH:
            errors["name"] = f"El nombre no puede exceder {self.MAX_NAME_LENGTH} caracteres"
        
        # Validar email
        if not email or not self._is_valid_email(email):
            errors["email"] = "Email inválido"
        
        # Validar tipo de proyecto
        valid_types = [pt.value for pt in ProjectType]
        if project_type not in valid_types:
            errors["project_type"] = f"Tipo de proyecto inválido. Opciones: {', '.join(valid_types)}"
        
        # Validar mensaje
        if not message or len(message.strip()) < self.MIN_MESSAGE_LENGTH:
            errors["message"] = f"El mensaje debe tener al menos {self.MIN_MESSAGE_LENGTH} caracteres"
        elif len(message) > self.MAX_MESSAGE_LENGTH:
            errors["message"] = f"El mensaje no puede exceder {self.MAX_MESSAGE_LENGTH} caracteres"
        
        return errors
    
    def _is_valid_email(self, email: str) -> bool:
        """Validación básica de email."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def create_contact(
        self,
        name: str,
        email: str,
        project_type: str,
        message: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Contact:
        """
        Crea un nuevo mensaje de contacto.
        
        Raises:
            ValueError: Si los datos son inválidos
        """
        errors = self.validate_contact_data(name, email, project_type, message)
        if errors:
            raise ValueError(errors)
        
        contact = Contact(
            name=name.strip(),
            email=email.strip().lower(),
            project_type=ProjectType(project_type),
            message=message.strip(),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return self.contact_repository.save(contact)
    
    def get_pending_count(self) -> int:
        """Obtiene el número de mensajes pendientes."""
        from ..entities.contact import ContactStatus
        return self.contact_repository.count(ContactStatus.PENDING)
    
    def get_project_types(self) -> List[Dict[str, str]]:
        """Retorna los tipos de proyecto disponibles."""
        return [
            {"value": ProjectType.WEB.value, "label": "Desarrollo web"},
            {"value": ProjectType.SECURITY.value, "label": "Consultoría de seguridad"},
            {"value": ProjectType.CTF.value, "label": "CTF / Red Team"},
            {"value": ProjectType.OTHER.value, "label": "Otro"},
        ]
