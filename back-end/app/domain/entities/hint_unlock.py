"""
Entidad HintUnlock - Pista desbloqueada por un jugador (con coste en puntos).
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class HintUnlock:
    """Un jugador desbloqueó la pista `hint_index` de un CTF pagando `cost` puntos.

    `cost` es una copia del coste en el momento del desbloqueo: si el admin
    cambia el coste después, el ranking no se reescribe.
    """

    user_id: UUID
    ctf_id: UUID
    hint_index: int
    cost: int = 0
    id: UUID = field(default_factory=uuid4)
    unlocked_at: datetime = field(default_factory=datetime.utcnow)
