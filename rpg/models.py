"""Data models for the RPG battle system."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Effect:
    """A single effect within a skill.

    effect_type:
        "damage"  – deal atk * coefficient damage to the target
        "heal"    – restore rcv * coefficient HP to self
        "status"  – apply a status effect with magnitude=coefficient to the target
    """

    effect_type: str
    coefficient: float
    status_name: Optional[str] = None  # required when effect_type == "status"

    def to_dict(self) -> dict:
        d = {"effect_type": self.effect_type, "coefficient": self.coefficient}
        if self.status_name is not None:
            d["status_name"] = self.status_name
        return d


@dataclass
class Skill:
    """A skill composed of one or more effects executed in order."""

    name: str
    effects: List[Effect] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"name": self.name, "effects": [e.to_dict() for e in self.effects]}


@dataclass
class StatusEffect:
    """A status condition applied to a character."""

    name: str
    magnitude: float
    duration: int  # remaining turns

    def to_dict(self) -> dict:
        return {"name": self.name, "magnitude": self.magnitude, "duration": self.duration}


@dataclass
class Character:
    """A battle participant (player or enemy)."""

    name: str
    max_hp: int
    max_sp: int
    atk: int
    rcv: int
    speed: int
    action_count: int
    skills: List[Skill] = field(default_factory=list)
    status_effects: List[StatusEffect] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.hp: int = self.max_hp
        self.sp: int = self.max_sp

    # ------------------------------------------------------------------
    # Battle helpers
    # ------------------------------------------------------------------

    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: int) -> int:
        """Reduce HP by *amount* (clamped to 0). Returns actual damage taken."""
        amount = max(0, amount)
        actual = min(amount, self.hp)
        self.hp -= actual
        return actual

    def heal_hp(self, amount: int) -> int:
        """Increase HP by *amount* (clamped to max_hp). Returns actual HP restored."""
        amount = max(0, amount)
        actual = min(amount, self.max_hp - self.hp)
        self.hp += actual
        return actual

    def apply_status(self, status: "StatusEffect") -> None:
        """Apply a status effect, refreshing it if it already exists."""
        for existing in self.status_effects:
            if existing.name == status.name:
                existing.magnitude = status.magnitude
                existing.duration = status.duration
                return
        self.status_effects.append(status)

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "sp": self.sp,
            "max_sp": self.max_sp,
            "atk": self.atk,
            "rcv": self.rcv,
            "speed": self.speed,
            "action_count": self.action_count,
            "skills": [s.to_dict() for s in self.skills],
            "status_effects": [se.to_dict() for se in self.status_effects],
        }
