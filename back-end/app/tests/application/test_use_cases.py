"""
Tests para los casos de uso.
"""

import pytest
from unittest.mock import Mock, MagicMock
from uuid import uuid4

from ...application.dto.ctf_dto import CTFCreateDTO
from ...application.use_cases.create_ctf import CreateCTFUseCase
from ...domain.entities.ctf import CTF, CTFLevel, CTFCategory


class TestCreateCTFUseCase:
    """Tests para el caso de uso CreateCTF."""
    
    def test_create_ctf_success(self):
        """Test: crear CTF exitosamente."""
        # Mock del repositorio
        mock_repo = Mock()
        mock_repo.save.return_value = CTF(
            title="Test CTF",
            level=CTFLevel.EASY,
            category=CTFCategory.WEB,
            platform="HackTheBox",
        )
        
        # Mock del servicio
        mock_service = Mock()
        mock_service.validate_ctf_data.return_value = {}
        mock_service.calculate_points.return_value = 20
        
        # Ejecutar caso de uso
        use_case = CreateCTFUseCase(mock_repo, mock_service)
        
        dto = CTFCreateDTO(
            title="Test CTF",
            level="easy",
            category="web",
            platform="HackTheBox",
        )
        
        result = use_case.execute(dto)
        
        assert result.title == "Test CTF"
        assert result.level == "easy"
        mock_repo.save.assert_called_once()
    
    def test_create_ctf_validation_error(self):
        """Test: título < 3 chars lo rechaza CTFCreateDTO (min_length=3)."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CTFCreateDTO(
                title="AB",  # Muy corto para el DTO
                level="easy",
                category="web",
                platform="HackTheBox",
            )
