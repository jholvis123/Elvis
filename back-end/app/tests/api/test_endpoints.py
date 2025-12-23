"""
Tests para los endpoints de la API.
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests para el endpoint de health check."""
    
    def test_health_check(self, client: TestClient):
        """Test: endpoint de health check responde correctamente."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestAuthEndpoints:
    """Tests para los endpoints de autenticación."""
    
    def test_register_user(self, client: TestClient):
        """Test: registrar un nuevo usuario."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "securepassword123",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"
    
    def test_register_duplicate_email(self, client: TestClient):
        """Test: no permitir emails duplicados."""
        # Primer registro
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser1",
                "password": "securepassword123",
            },
        )
        
        # Segundo registro con mismo email
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser2",
                "password": "securepassword123",
            },
        )
        
        assert response.status_code == 400
    
    def test_login_success(self, client: TestClient):
        """Test: login exitoso."""
        # Primero registrar
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "securepassword123",
            },
        )
        
        # Luego login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "securepassword123",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client: TestClient):
        """Test: login con credenciales inválidas."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword",
            },
        )
        
        assert response.status_code == 401


class TestCTFEndpoints:
    """Tests para los endpoints de CTFs."""
    
    def test_list_ctfs_empty(self, client: TestClient):
        """Test: listar CTFs cuando no hay ninguno."""
        response = client.get("/api/v1/ctfs")
        
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
    
    def test_get_ctf_statistics(self, client: TestClient):
        """Test: obtener estadísticas de CTFs."""
        response = client.get("/api/v1/ctfs/statistics")
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "solved" in data
        assert "by_level" in data
        assert "by_category" in data
