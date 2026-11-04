"""
Router de CTFs.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request

from ...application.dto.ctf_dto import (
    CTFCreateDTO,
    CTFUpdateDTO,
    CTFResponseDTO,
    CTFListResponseDTO,
    CTFStatisticsDTO,
)
from ...application.dto.flag_dto import (
    FlagSubmitDTO,
    FlagSubmitResponseDTO,
    LeaderboardEntryDTO,
    LeaderboardResponseDTO,
    UserStatsDTO,
    SolvedCTFDTO,
    HintUnlockResponseDTO,
    CTFSolveDTO,
    CTFSolvesResponseDTO,
    BoardChallengeDTO,
    BoardCategoryDTO,
    BoardResponseDTO,
)
from ...application.use_cases import (
    CreateCTFUseCase,
    ListCTFsUseCase,
    GetCTFUseCase,
    UpdateCTFUseCase,
    DeleteCTFUseCase,
)
from ...core.security_middleware import limiter, RATE_LIMITS
from ...domain.entities.user import User
from ...domain.entities.ctf import CTF, CTFStatus
from ...domain.repositories.ctf_repo import CTFRepository
from ...domain.repositories.writeup_repo import WriteupRepository
from ...domain.repositories.flag_submission_repo import FlagSubmissionRepository
from ...domain.services.ctf_service import CTFService
from ...domain.services.flag_service import FlagService
from ...domain.services.scoreboard_service import ScoreboardService
from ...domain.entities.hint_unlock import HintUnlock
from ...domain.repositories.hint_unlock_repo import HintUnlockRepository
from ..dependencies import (
    get_ctf_repository,
    get_writeup_repository,
    get_ctf_service,
    get_flag_service,
    get_current_user,
    get_current_admin,
    get_current_user_optional,
    get_flag_submission_repository,
    get_hint_unlock_repository,
    get_scoreboard_service,
)

router = APIRouter(prefix="/ctfs", tags=["CTFs"])


def _ensure_ctf_visible(ctf: CTF, current_user: Optional[User]) -> None:
    """404 unpublished CTFs unless the requester is admin (no existence leak)."""
    if ctf.status == CTFStatus.PUBLISHED:
        return
    if current_user is not None and current_user.is_admin:
        return
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="CTF not found",
    )


def _apply_hint_visibility(
    items: List[CTFResponseDTO],
    current_user: Optional[User],
    hint_repo: HintUnlockRepository,
) -> None:
    """Oculta (None) las pistas con coste que quien consulta no desbloqueó.

    Admin ve todas. Pistas con coste 0 son siempre visibles.
    """
    if current_user is not None and current_user.is_admin:
        for item in items:
            item.unlocked_hints = list(range(len(item.hints)))
        return
    unlocked = (
        hint_repo.unlocked_indexes(current_user.id, [i.id for i in items])
        if current_user is not None
        else {}
    )
    for item in items:
        mine = set(unlocked.get(item.id, []))
        costs = item.hint_costs
        visible = []
        for index, text in enumerate(item.hints):
            cost = costs[index] if index < len(costs) else 0
            visible.append(text if cost <= 0 or index in mine else None)
        item.hints = visible
        item.unlocked_hints = sorted(
            i for i in range(len(item.hints))
            if (costs[i] if i < len(costs) else 0) <= 0 or i in mine
        )


@router.get("/admin/all", response_model=CTFListResponseDTO)
async def list_all_ctfs_admin(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    level: Optional[str] = None,
    category: Optional[str] = None,
    platform: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_admin),
    ctf_repo: CTFRepository = Depends(get_ctf_repository),
    writeup_repo: WriteupRepository = Depends(get_writeup_repository),
):
    """Lista TODOS los CTFs para administradores (incluye drafts y archivados)."""
    use_case = ListCTFsUseCase(ctf_repo, writeup_repo)
    
    return use_case.execute_admin(
        page=page,
        size=size,
        level=level,
        category=category,
        platform=platform,
        status=status,
        search=search,
    )


@router.get("", response_model=CTFListResponseDTO)
async def list_ctfs(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    level: Optional[str] = None,
    category: Optional[str] = None,
    platform: Optional[str] = None,
    search: Optional[str] = None,
    ctf_repo: CTFRepository = Depends(get_ctf_repository),
    writeup_repo: WriteupRepository = Depends(get_writeup_repository),
    current_user: Optional[User] = Depends(get_current_user_optional),
    hint_repo: HintUnlockRepository = Depends(get_hint_unlock_repository),
):
    """Lista CTFs con filtros y paginación."""
    use_case = ListCTFsUseCase(ctf_repo, writeup_repo)
    
    result = use_case.execute(
        page=page,
        size=size,
        level=level,
        category=category,
        platform=platform,
        search=search,
    )
    _apply_hint_visibility(result.items, current_user, hint_repo)
    return result


@router.get("/board", response_model=BoardResponseDTO)
async def get_board(
    ctf_repo: CTFRepository = Depends(get_ctf_repository),
    writeup_repo: WriteupRepository = Depends(get_writeup_repository),
    scoreboard: ScoreboardService = Depends(get_scoreboard_service),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Tablero estilo CTFd: retos publicados y activos agrupados por categoría."""
    ctfs = [c for c in ctf_repo.get_published(limit=1000) if c.is_active]
    counts = scoreboard.solve_counts()
    mine = scoreboard.solved_ctf_ids(current_user.id) if current_user else set()

    by_category: dict = {}
    for ctf in sorted(ctfs, key=lambda c: (c.points, c.title.lower())):
        by_category.setdefault(ctf.category.value, []).append(
            BoardChallengeDTO(
                id=ctf.id,
                title=ctf.title,
                level=ctf.level.value,
                points=ctf.points,
                solves=counts.get(ctf.id, 0),
                solved_by_me=ctf.id in mine,
                has_writeup=writeup_repo.get_by_ctf_id(ctf.id) is not None,
            )
        )

    my_score = my_rank = None
    if current_user is not None and not current_user.is_admin:
        entry = scoreboard.user_entry(current_user.id)
        my_score = entry.score if entry else 0
        my_rank = entry.rank if entry else None

    return BoardResponseDTO(
        categories=[
            BoardCategoryDTO(category=cat, challenges=items)
            for cat, items in sorted(by_category.items())
        ],
        total=len(ctfs),
        solved_by_me=len(mine & {c.id for c in ctfs}),
        my_score=my_score,
        my_rank=my_rank,
    )


@router.get("/statistics", response_model=CTFStatisticsDTO)
async def get_statistics(
    ctf_repo: CTFRepository = Depends(get_ctf_repository),
    writeup_repo: WriteupRepository = Depends(get_writeup_repository),
):
    """Obtiene estadísticas de CTFs."""
    use_case = ListCTFsUseCase(ctf_repo, writeup_repo)
    return use_case.get_statistics()


@router.get("/{ctf_id}", response_model=CTFResponseDTO)
async def get_ctf(
    ctf_id: UUID,
    ctf_repo: CTFRepository = Depends(get_ctf_repository),
    writeup_repo: WriteupRepository = Depends(get_writeup_repository),
    current_user: Optional[User] = Depends(get_current_user_optional),
    hint_repo: HintUnlockRepository = Depends(get_hint_unlock_repository),
):
    """Obtiene un CTF por su ID."""
    is_admin = current_user is not None and current_user.is_admin
    use_case = GetCTFUseCase(ctf_repo, writeup_repo)
    result = use_case.execute(ctf_id, is_admin=is_admin)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CTF not found",
        )
    
    _apply_hint_visibility([result], current_user, hint_repo)
    return result


@router.get("/{ctf_id}/solves", response_model=CTFSolvesResponseDTO)
async def get_ctf_solves(
    ctf_id: UUID,
    ctf_repo: CTFRepository = Depends(get_ctf_repository),
    scoreboard: ScoreboardService = Depends(get_scoreboard_service),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Jugadores que resolvieron el reto, del primero (primera sangre) al último."""
    ctf = ctf_repo.get_by_id(ctf_id)
    if not ctf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CTF not found")
    _ensure_ctf_visible(ctf, current_user)

    solves = scoreboard.ctf_solves(ctf_id)
    return CTFSolvesResponseDTO(
        items=[
            CTFSolveDTO(username=s.username, solved_at=s.solved_at, first_blood=i == 0)
            for i, s in enumerate(solves)
        ],
        total=len(solves),
    )


@router.post("/{ctf_id}/hints/{index}/unlock", response_model=HintUnlockResponseDTO)
@limiter.limit(RATE_LIMITS["hint_unlock"])
async def unlock_hint(
    request: Request,
    ctf_id: UUID,
    index: int,
    ctf_repo: CTFRepository = Depends(get_ctf_repository),
    hint_repo: HintUnlockRepository = Depends(get_hint_unlock_repository),
    current_user: User = Depends(get_current_user),
):
    """Desbloquea una pista. Su coste se resta del puntaje del jugador en el ranking.

    Idempotente: repetir no cobra dos veces. El admin la ve sin coste.
    """
    ctf = ctf_repo.get_by_id(ctf_id)
    if not ctf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CTF not found")
    _ensure_ctf_visible(ctf, current_user)
    if not ctf.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This challenge is not active",
        )
    if index < 0 or index >= len(ctf.hints):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hint not found")

    cost = ctf.hint_cost(index)
    if current_user.is_admin or cost <= 0:
        return HintUnlockResponseDTO(index=index, hint=ctf.hints[index], cost=0)

    existing = hint_repo.get(current_user.id, ctf_id, index)
    if existing is not None:
        return HintUnlockResponseDTO(
            index=index, hint=ctf.hints[index], cost=existing.cost, already_unlocked=True
        )

    new_unlock = HintUnlock(user_id=current_user.id, ctf_id=ctf_id, hint_index=index, cost=cost)
    saved = hint_repo.save(new_unlock)
    return HintUnlockResponseDTO(
        index=index,
        hint=ctf.hints[index],
        cost=saved.cost,
        # Otra petición simultánea pudo crear la fila primero: no se cobra dos veces
        already_unlocked=saved.id != new_unlock.id,
    )


@router.post("", response_model=CTFResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_ctf(
    data: CTFCreateDTO,
    current_user: User = Depends(get_current_admin),
    ctf_repo: CTFRepository = Depends(get_ctf_repository),
    ctf_service: CTFService = Depends(get_ctf_service),
):
    """Crea un nuevo CTF (requiere admin)."""
    use_case = CreateCTFUseCase(ctf_repo, ctf_service)
    
    try:
        return use_case.execute(data, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/{ctf_id}", response_model=CTFResponseDTO)
async def update_ctf(
    ctf_id: UUID,
    data: CTFUpdateDTO,
    current_user: User = Depends(get_current_admin),
    ctf_repo: CTFRepository = Depends(get_ctf_repository),
    writeup_repo: WriteupRepository = Depends(get_writeup_repository),
    ctf_service: CTFService = Depends(get_ctf_service),
):
    """Actualiza un CTF existente (requiere admin)."""
    use_case = UpdateCTFUseCase(ctf_repo, writeup_repo, ctf_service)
    
    try:
        result = use_case.execute(ctf_id, data, user_id=current_user.id)
    except ValueError as e:
        # Regex de flag inválido o demasiado largo → 400, no 500
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CTF not found",
        )
    
    return result


@router.post("/{ctf_id}/publish", response_model=CTFResponseDTO)
async def publish_ctf(
    ctf_id: UUID,
    current_user: User = Depends(get_current_admin),
    ctf_repo: CTFRepository = Depends(get_ctf_repository),
    writeup_repo: WriteupRepository = Depends(get_writeup_repository),
    ctf_service: CTFService = Depends(get_ctf_service),
):
    """Publica un CTF (requiere admin)."""
    use_case = UpdateCTFUseCase(ctf_repo, writeup_repo, ctf_service)
    
    try:
        result = use_case.publish(ctf_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CTF not found",
            )
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{ctf_id}/submit", response_model=FlagSubmitResponseDTO)
@limiter.limit(RATE_LIMITS["flag_submit"])
async def submit_flag(
    ctf_id: UUID,
    data: FlagSubmitDTO,
    request: Request,
    ctf_repo: CTFRepository = Depends(get_ctf_repository),
    flag_service: FlagService = Depends(get_flag_service),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Envía una flag para validación.

    Rate limit compartido (~20/minuto por IP). La respuesta nunca incluye
    la flag correcta ni el valor enviado.
    """
    # Obtener el CTF
    ctf = ctf_repo.get_by_id(ctf_id)
    if not ctf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CTF not found",
        )

    # Unpublished (draft/archived) → 404 for non-admin even if is_active
    _ensure_ctf_visible(ctf, current_user)
    
    # Verificar si el CTF está activo
    if not ctf.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This challenge is not active",
        )
    
    # Sin request.client no hay IP. solved_count no se incrementa en ese caso,
    # ni para anónimos ni para un no-admin autenticado. Un admin marca solved
    # y solved_at y tampoco incrementa el contador.
    ip_address = request.client.host if request.client else None
    user_id = current_user.id if current_user else None
    is_admin = current_user is not None and current_user.is_admin
    
    # Intentar enviar la flag
    try:
        is_correct, message, points = flag_service.submit_flag(
            ctf_id=ctf_id,
            flag=data.flag,
            user_id=user_id,
            ip_address=ip_address,
            is_admin=is_admin,
        )
        
        return FlagSubmitResponseDTO(
            success=is_correct,
            is_correct=is_correct,
            message=message,
            points=points,
        )
    except ValueError:
        # No filtrar el valor de la flag ni detalles internos
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to validate flag",
        )


@router.delete("/{ctf_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ctf(
    ctf_id: UUID,
    force: bool = False,
    current_user: User = Depends(get_current_admin),
    ctf_repo: CTFRepository = Depends(get_ctf_repository),
    writeup_repo: WriteupRepository = Depends(get_writeup_repository),
):
    """Elimina un CTF (requiere admin)."""
    use_case = DeleteCTFUseCase(ctf_repo, writeup_repo)
    
    try:
        deleted = use_case.execute(ctf_id, force=force)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CTF not found",
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =============================================
# LEADERBOARD / RANKING ENDPOINTS
# =============================================

def _solved_ctf_dtos(entry) -> List[SolvedCTFDTO]:
    return [
        SolvedCTFDTO(
            id=str(solve.ctf_id),
            title=solve.ctf_title,
            points=solve.points,
            category=solve.category,
            level=solve.level,
            solved_at=solve.solved_at.isoformat() if solve.solved_at else None,
        )
        for solve in sorted(entry.solves, key=lambda x: x.solved_at, reverse=True)
    ]


@router.get("/leaderboard/top", response_model=LeaderboardResponseDTO, tags=["Leaderboard"])
async def get_leaderboard(
    limit: int = Query(10, ge=1, le=100, description="Número de jugadores en el ranking"),
    scoreboard: ScoreboardService = Depends(get_scoreboard_service),
):
    """
    Ranking de jugadores: puntos de retos publicados menos coste de pistas.

    Excluye admins e inactivos. Empate: gana quien llegó antes a su puntuación.
    """
    ranking = scoreboard.ranking()
    entries = [
        LeaderboardEntryDTO(
            rank=entry.rank,
            user_id=str(entry.user_id),
            username=entry.username,
            total_points=entry.score,
            solved_count=entry.solved_count,
            hint_penalty=entry.hint_penalty,
            last_solve_at=entry.last_solve_at,
        )
        for entry in ranking[:limit]
    ]
    return LeaderboardResponseDTO(
        entries=entries,
        total_players=len(ranking),
        updated_at=datetime.utcnow(),
    )


@router.get("/leaderboard/me", response_model=UserStatsDTO, tags=["Leaderboard"])
async def get_my_stats(
    current_user: User = Depends(get_current_user),
    scoreboard: ScoreboardService = Depends(get_scoreboard_service),
):
    """Estadísticas del jugador autenticado: puntos, posición y retos resueltos."""
    entry = scoreboard.user_entry(current_user.id)
    if entry is None:
        return UserStatsDTO(
            user_id=str(current_user.id),
            username=current_user.username,
            total_points=0,
            solved_count=0,
            rank=None,
            solved_ctfs=[],
        )
    return UserStatsDTO(
        user_id=str(entry.user_id),
        username=entry.username,
        total_points=entry.score,
        solved_count=entry.solved_count,
        rank=entry.rank,
        solved_ctfs=_solved_ctf_dtos(entry),
    )


@router.get("/leaderboard/user/{user_id}", response_model=UserStatsDTO, tags=["Leaderboard"])
async def get_user_stats(
    user_id: UUID,
    scoreboard: ScoreboardService = Depends(get_scoreboard_service),
):
    """Estadísticas públicas de un jugador del ranking."""
    entry = scoreboard.user_entry(user_id)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or has no CTF activity",
        )
    return UserStatsDTO(
        user_id=str(entry.user_id),
        username=entry.username,
        total_points=entry.score,
        solved_count=entry.solved_count,
        rank=entry.rank,
        solved_ctfs=_solved_ctf_dtos(entry),
    )
