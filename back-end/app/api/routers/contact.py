"""
Router de Contact - Formulario de contacto.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request

from ...application.dto.contact_dto import (
    ContactCreateDTO,
    ContactResponseDTO,
    ContactListResponseDTO,
)
from ...domain.entities.contact import ContactStatus
from ...domain.services.contact_service import ContactService
from ..dependencies import get_contact_service, get_current_admin


router = APIRouter(prefix="/contact", tags=["Contact"])


@router.post(
    "",
    response_model=ContactResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Enviar mensaje de contacto",
)
async def send_contact_message(
    contact_data: ContactCreateDTO,
    request: Request,
    contact_service: ContactService = Depends(get_contact_service),
) -> ContactResponseDTO:
    """
    Envía un nuevo mensaje de contacto.
    
    - **name**: Nombre del remitente
    - **email**: Email de contacto
    - **project_type**: Tipo de proyecto
    - **message**: Mensaje del formulario
    """
    # Obtener metadatos de la petición
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    try:
        contact = contact_service.create_contact(
            name=contact_data.name,
            email=contact_data.email,
            project_type=contact_data.project_type.value,
            message=contact_data.message,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return ContactResponseDTO(
            id=contact.id,
            name=contact.name,
            email=contact.email,
            project_type=contact.project_type.value,
            message=contact.message,
            status=contact.status.value,
            created_at=contact.created_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "",
    response_model=ContactListResponseDTO,
    summary="Listar mensajes de contacto",
    dependencies=[Depends(get_current_admin)],
)
async def list_contact_messages(
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    contact_service: ContactService = Depends(get_contact_service),
) -> ContactListResponseDTO:
    """
    Lista todos los mensajes de contacto (solo admin).
    
    - **status_filter**: Filtrar por estado (pending, read, replied)
    - **skip**: Número de registros a omitir
    - **limit**: Número máximo de registros
    """
    contact_status = None
    if status_filter:
        try:
            contact_status = ContactStatus(status_filter)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estado inválido: {status_filter}",
            )
    
    contacts = contact_service.contact_repo.get_all(
        status=contact_status,
        skip=skip,
        limit=limit,
    )
    total = contact_service.contact_repo.count(status=contact_status)
    
    return ContactListResponseDTO(
        items=[
            ContactResponseDTO(
                id=c.id,
                name=c.name,
                email=c.email,
                project_type=c.project_type.value,
                message=c.message,
                status=c.status.value,
                created_at=c.created_at,
                read_at=c.read_at,
                replied_at=c.replied_at,
            )
            for c in contacts
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/project-types",
    response_model=List[dict],
    summary="Obtener tipos de proyecto",
)
async def get_project_types(
    contact_service: ContactService = Depends(get_contact_service),
) -> List[dict]:
    """
    Obtiene la lista de tipos de proyecto disponibles.
    """
    return contact_service.get_project_types()


@router.get(
    "/{contact_id}",
    response_model=ContactResponseDTO,
    summary="Obtener mensaje por ID",
    dependencies=[Depends(get_current_admin)],
)
async def get_contact_message(
    contact_id: UUID,
    contact_service: ContactService = Depends(get_contact_service),
) -> ContactResponseDTO:
    """
    Obtiene un mensaje de contacto por su ID (solo admin).
    """
    contact = contact_service.contact_repo.get_by_id(contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mensaje no encontrado",
        )
    
    return ContactResponseDTO(
        id=contact.id,
        name=contact.name,
        email=contact.email,
        project_type=contact.project_type.value,
        message=contact.message,
        status=contact.status.value,
        created_at=contact.created_at,
        read_at=contact.read_at,
        replied_at=contact.replied_at,
    )


@router.patch(
    "/{contact_id}/mark-read",
    response_model=ContactResponseDTO,
    summary="Marcar como leído",
    dependencies=[Depends(get_current_admin)],
)
async def mark_as_read(
    contact_id: UUID,
    contact_service: ContactService = Depends(get_contact_service),
) -> ContactResponseDTO:
    """
    Marca un mensaje como leído (solo admin).
    """
    contact = contact_service.mark_as_read(contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mensaje no encontrado",
        )
    
    return ContactResponseDTO(
        id=contact.id,
        name=contact.name,
        email=contact.email,
        project_type=contact.project_type.value,
        message=contact.message,
        status=contact.status.value,
        created_at=contact.created_at,
        read_at=contact.read_at,
        replied_at=contact.replied_at,
    )


@router.patch(
    "/{contact_id}/mark-replied",
    response_model=ContactResponseDTO,
    summary="Marcar como respondido",
    dependencies=[Depends(get_current_admin)],
)
async def mark_as_replied(
    contact_id: UUID,
    contact_service: ContactService = Depends(get_contact_service),
) -> ContactResponseDTO:
    """
    Marca un mensaje como respondido (solo admin).
    """
    contact = contact_service.mark_as_replied(contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mensaje no encontrado",
        )
    
    return ContactResponseDTO(
        id=contact.id,
        name=contact.name,
        email=contact.email,
        project_type=contact.project_type.value,
        message=contact.message,
        status=contact.status.value,
        created_at=contact.created_at,
        read_at=contact.read_at,
        replied_at=contact.replied_at,
    )


@router.delete(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar mensaje",
    dependencies=[Depends(get_current_admin)],
)
async def delete_contact_message(
    contact_id: UUID,
    contact_service: ContactService = Depends(get_contact_service),
) -> None:
    """
    Elimina un mensaje de contacto (solo admin).
    """
    deleted = contact_service.contact_repo.delete(contact_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mensaje no encontrado",
        )
