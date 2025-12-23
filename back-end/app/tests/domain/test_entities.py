"""
Tests para las entidades del dominio.
"""

import pytest
from datetime import datetime

from ...domain.entities.ctf import CTF, CTFLevel, CTFCategory, CTFStatus
from ...domain.entities.user import User
from ...domain.entities.project import Project, ProjectStatus
from ...domain.entities.writeup import Writeup, WriteupStatus


class TestCTFEntity:
    """Tests para la entidad CTF."""
    
    def test_create_ctf(self):
        """Test: crear un CTF con datos válidos."""
        ctf = CTF(
            title="Test CTF",
            level=CTFLevel.EASY,
            category=CTFCategory.WEB,
            platform="HackTheBox",
        )
        
        assert ctf.title == "Test CTF"
        assert ctf.level == CTFLevel.EASY
        assert ctf.category == CTFCategory.WEB
        assert ctf.status == CTFStatus.DRAFT
        assert ctf.solved is False
    
    def test_mark_as_solved(self):
        """Test: marcar CTF como resuelto."""
        ctf = CTF(
            title="Test CTF",
            level=CTFLevel.MEDIUM,
            category=CTFCategory.PWN,
            platform="TryHackMe",
        )
        
        ctf.mark_as_solved()
        
        assert ctf.solved is True
        assert ctf.solved_at is not None
    
    def test_publish_ctf(self):
        """Test: publicar un CTF."""
        ctf = CTF(
            title="Test CTF",
            level=CTFLevel.HARD,
            category=CTFCategory.REVERSE,
            platform="CTFtime",
        )
        
        ctf.publish()
        
        assert ctf.status == CTFStatus.PUBLISHED
        assert ctf.is_published is True
    
    def test_add_tag(self):
        """Test: añadir tags a un CTF."""
        ctf = CTF(
            title="Test CTF",
            level=CTFLevel.EASY,
            category=CTFCategory.WEB,
            platform="HackTheBox",
        )
        
        ctf.add_tag("sql-injection")
        ctf.add_tag("xss")
        ctf.add_tag("sql-injection")  # Duplicado
        
        assert len(ctf.tags) == 2
        assert "sql-injection" in ctf.tags
        assert "xss" in ctf.tags


class TestUserEntity:
    """Tests para la entidad User."""
    
    def test_create_user(self):
        """Test: crear un usuario."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpassword",
        )
        
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.is_active is True
        assert user.is_admin is False
    
    def test_deactivate_user(self):
        """Test: desactivar usuario."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpassword",
        )
        
        user.deactivate()
        
        assert user.is_active is False
    
    def test_promote_to_admin(self):
        """Test: promover usuario a admin."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpassword",
        )
        
        user.promote_to_admin()
        
        assert user.is_admin is True


class TestProjectEntity:
    """Tests para la entidad Project."""
    
    def test_create_project(self):
        """Test: crear un proyecto."""
        project = Project(
            title="Test Project",
            description="A test project description",
        )
        
        assert project.title == "Test Project"
        assert project.status == ProjectStatus.DRAFT
        assert project.featured is False
    
    def test_publish_project(self):
        """Test: publicar proyecto."""
        project = Project(
            title="Test Project",
            description="A test project description",
        )
        
        project.publish()
        
        assert project.status == ProjectStatus.PUBLISHED
    
    def test_add_technology(self):
        """Test: añadir tecnología a proyecto."""
        project = Project(
            title="Test Project",
            description="A test project description",
        )
        
        project.add_technology("Python")
        project.add_technology("FastAPI")
        
        assert len(project.technologies) == 2
        assert "Python" in project.technologies
