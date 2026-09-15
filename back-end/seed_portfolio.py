#!/usr/bin/env python3
"""
Seed idempotente de proyectos del portafolio (contenido real de GitHub).

No inventa CTFs ni flags. No inventa writeups.

Uso local:
  SEED_PORTFOLIO=1 DATABASE_URL=... python seed_portfolio.py

Render (one-shot):
  1) En el servicio, añade env SEED_PORTFOLIO=1
  2) startCommand temporal:
       alembic upgrade head && python seed_portfolio.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT
  3) Tras un deploy exitoso y GET /api/v1/projects?size=20 con total>=4 published,
     quita SEED_PORTFOLIO y vuelve al startCommand normal:
       alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT

Idempotencia: no duplica filas con el mismo github_url (ni el mismo title si github_url vacío).
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

from app.infrastructure.persistence.models.project_model import ProjectModel


def normalize_database_url(url: str) -> str:
    """Misma normalización que Settings: Render suele inyectar postgres://."""
    if url.startswith("postgres://"):
        return "postgresql+psycopg2://" + url[len("postgres://") :]
    if url.startswith("postgresql://") and "+psycopg" not in url.split("://", 1)[0]:
        return "postgresql+psycopg2://" + url[len("postgresql://") :]
    return url


# Fuentes: metadatos públicos de https://github.com/jholvis123/<repo>
# (descripciones/README/homepage/fork parent consultados vía API GitHub; sin inventar).
SEED_PROJECTS: List[Dict[str, Any]] = [
    {
        "title": "Elvis — Portafolio personal",
        "github_url": "https://github.com/jholvis123/Elvis",
        "demo_url": "https://jholvis123.github.io/Elvis/",
        "short_description": "Creacion de mi portafolio",
        "description": (
            "Portafolio fullstack personal (repo jholvis123/Elvis). "
            "Backend FastAPI con arquitectura Clean/Hexagonal, JWT, proyectos, CTFs y writeups; "
            "frontend Angular. Descripción en GitHub: «Creacion de mi portafolio». "
            "Lenguajes principales en el repo: Python y TypeScript (también HTML/SCSS/Docker)."
        ),
        "technologies": [
            "Python",
            "FastAPI",
            "TypeScript",
            "Angular",
            "SQLAlchemy",
            "Docker",
        ],
        "highlights": [
            "API FastAPI + frontend Angular en el mismo monorepo",
            "Despliegue frontend en GitHub Pages (/Elvis/)",
            "Backend preparado para Postgres en Render",
        ],
        "featured": True,
        "order": 1,
    },
    {
        "title": "CTFd (fork)",
        "github_url": "https://github.com/jholvis123/CTFd",
        "demo_url": "https://ctfd.io",
        "short_description": "CTFs as you need them",
        "description": (
            "Fork personal de CTFd/CTFd (https://github.com/CTFd/CTFd), framework open source "
            "para organizar Capture The Flag. La descripción del repo es la del upstream: "
            "«CTFs as you need them». El README upstream documenta retos dinámicos, flags "
            "estáticas/regex, scoreboard, equipos, temas/plugins y despliegue con Docker. "
            "Este proyecto en jholvis123 es un fork para estudio/despliegue — no es una "
            "plataforma CTF escrita desde cero."
        ),
        "technologies": ["Python", "JavaScript", "HTML", "Vue", "Docker"],
        "highlights": [
            "Fork de CTFd/CTFd (no código original propio del framework)",
            "Stack upstream: Python + JS/Vue según languages del repo",
            "Homepage del repo apunta a https://ctfd.io",
        ],
        "featured": True,
        "order": 2,
    },
    {
        "title": "Global — Sistema de gestión de autotransporte",
        "github_url": "https://github.com/jholvis123/Global-",
        "demo_url": None,
        "short_description": "sistema de gestion",
        "description": (
            "Sistema integral de gestión para empresa de autotransporte pesado "
            "(repo jholvis123/Global-). Según el README del repositorio: Angular 17+ "
            "(frontend), FastAPI (backend) y SQL Server; módulos de socios, choferes, "
            "vehículos, viajes, liquidaciones y reportes; autenticación JWT con roles; "
            "localización Bolivia (America/La_Paz, Bs)."
        ),
        "technologies": [
            "Python",
            "FastAPI",
            "TypeScript",
            "Angular",
            "SQL Server",
            "Docker",
            "JWT",
        ],
        "highlights": [
            "Gestión de socios, choferes, vehículos y viajes (README)",
            "JWT con roles (Admin, Operaciones, Finanzas, Socio, Chofer, Cliente)",
            "Docker Compose + Nginx documentados en el README",
        ],
        "featured": False,
        "order": 4,
    },
    {
        "title": "fastapi-product — API de productos y tareas (fork)",
        "github_url": "https://github.com/jholvis123/fastapi-product",
        "demo_url": "https://fastapi-product.vercel.app",
        "short_description": "Lista de Productos y Tareas",
        "description": (
            "Fork personal de henrytaby/fastapi-product. Descripción en GitHub: "
            "«Lista de Productos y Tareas». El README del repo describe una API FastAPI "
            "modular (productos, tareas, categorías, marcas) con patrón repositorio, "
            "JWT con rotación/blacklist, auditoría y PostgreSQL/SQLModel. "
            "Homepage del repo: https://fastapi-product.vercel.app."
        ),
        "technologies": ["Python", "FastAPI", "SQLModel", "PostgreSQL", "JWT", "Pydantic"],
        "highlights": [
            "Fork de henrytaby/fastapi-product (upstream documentado en el README)",
            "Arquitectura modular + repositorio (README)",
            "Demo/homepage del repo en Vercel",
        ],
        "featured": False,
        "order": 5,
    },
    {
        "title": "Trabajo Final de Seguridad",
        "github_url": "https://github.com/jholvis123/Trabajo-Final-De-Seguridad",
        "demo_url": None,
        "short_description": "trabnajo final",
        "description": (
            "Repositorio jholvis123/Trabajo-Final-De-Seguridad. Descripción pública en "
            "GitHub: «trabnajo final». Al momento del seed, el árbol público visible vía "
            "API contiene principalmente configuración bajo .github/ (sin README ni "
            "lenguajes detectados). Se publica el enlace real al repo sin inventar "
            "alcance técnico adicional."
        ),
        "technologies": [],
        "highlights": [
            "Repo real en GitHub (jholvis123/Trabajo-Final-De-Seguridad)",
            "Contenido público limitado al momento del seed — sin inventar stack",
        ],
        "featured": True,
        "order": 3,
    },
]


def _find_existing(db, github_url: Optional[str], title: str) -> Optional[ProjectModel]:
    if github_url:
        found = db.query(ProjectModel).filter(ProjectModel.github_url == github_url).first()
        if found:
            return found
    return db.query(ProjectModel).filter(ProjectModel.title == title).first()


def seed_projects(db) -> Tuple[int, int]:
    """Inserta o actualiza proyectos. Returns (created, updated)."""
    created = 0
    updated = 0
    now = datetime.utcnow()
    for item in SEED_PROJECTS:
        existing = _find_existing(db, item.get("github_url"), item["title"])
        tech_json = json.dumps(item.get("technologies") or [], ensure_ascii=False)
        highlights_json = json.dumps(item.get("highlights") or [], ensure_ascii=False)
        if existing:
            existing.title = item["title"]
            existing.description = item["description"]
            existing.short_description = item.get("short_description")
            existing.github_url = item.get("github_url")
            existing.demo_url = item.get("demo_url")
            existing.technologies = tech_json
            existing.highlights = highlights_json
            existing.status = "published"
            existing.featured = bool(item.get("featured"))
            existing.order = int(item.get("order") or 0)
            existing.updated_at = now
            updated += 1
        else:
            db.add(
                ProjectModel(
                    id=str(uuid.uuid4()),
                    title=item["title"],
                    description=item["description"],
                    short_description=item.get("short_description"),
                    github_url=item.get("github_url"),
                    demo_url=item.get("demo_url"),
                    technologies=tech_json,
                    highlights=highlights_json,
                    status="published",
                    featured=bool(item.get("featured")),
                    order=int(item.get("order") or 0),
                    created_at=now,
                    updated_at=now,
                )
            )
            created += 1
    db.commit()
    return created, updated


def main() -> int:
    if os.getenv("SEED_PORTFOLIO", "").strip() not in {"1", "true", "True", "yes", "YES"}:
        print("SEED_PORTFOLIO no está activo — no-op (set SEED_PORTFOLIO=1 para sembrar).")
        return 0

    raw_url = os.getenv("DATABASE_URL")
    if not raw_url:
        print("Error: DATABASE_URL es obligatorio.")
        return 1

    url = normalize_database_url(raw_url)
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        created, updated = seed_projects(db)
        published = (
            db.query(ProjectModel).filter(ProjectModel.status == "published").count()
        )
        print(f"Seed OK — created={created} updated={updated} published_total={published}")
        print("CTFs/writeups: omitidos (sin contenido inventado).")
        return 0
    except Exception as exc:
        db.rollback()
        print(f"Seed FAILED: {exc}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
