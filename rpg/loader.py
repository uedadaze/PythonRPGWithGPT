"""JSON loading utilities for the RPG battle system."""

import json
from typing import Any, Dict, List

from .models import Character, Effect, Skill, StatusEffect


# ---------------------------------------------------------------------------
# Primitive loaders
# ---------------------------------------------------------------------------


def load_effect_from_dict(data: Dict[str, Any]) -> Effect:
    return Effect(
        effect_type=data["effect_type"],
        coefficient=float(data["coefficient"]),
        status_name=data.get("status_name"),
    )


def load_skill_from_dict(data: Dict[str, Any]) -> Skill:
    effects = [load_effect_from_dict(e) for e in data.get("effects", [])]
    return Skill(name=data["name"], effects=effects)


def load_status_effect_from_dict(data: Dict[str, Any]) -> StatusEffect:
    return StatusEffect(
        name=data["name"],
        magnitude=float(data["magnitude"]),
        duration=int(data["duration"]),
    )


def load_character_from_dict(data: Dict[str, Any]) -> Character:
    """Create a :class:`Character` from a plain dictionary."""
    skills = [load_skill_from_dict(s) for s in data.get("skills", [])]
    status_effects = [load_status_effect_from_dict(se) for se in data.get("status_effects", [])]
    char = Character(
        name=data["name"],
        max_hp=int(data["max_hp"]),
        max_sp=int(data["max_sp"]),
        atk=int(data["atk"]),
        rcv=int(data["rcv"]),
        speed=int(data["speed"]),
        action_count=int(data["action_count"]),
        skills=skills,
        status_effects=status_effects,
    )
    # Allow callers to supply a current HP/SP that differs from max
    if "hp" in data:
        char.hp = int(data["hp"])
    if "sp" in data:
        char.sp = int(data["sp"])
    return char


# ---------------------------------------------------------------------------
# File-based loaders
# ---------------------------------------------------------------------------


def load_characters_from_file(path: str) -> List[Character]:
    """Load one or more characters from a JSON file (dict or list of dicts)."""
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    if isinstance(raw, list):
        return [load_character_from_dict(d) for d in raw]
    return [load_character_from_dict(raw)]


def load_skills_from_file(path: str) -> List[Skill]:
    """Load a list of skills from a JSON file (single dict or list of dicts)."""
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    if isinstance(raw, list):
        return [load_skill_from_dict(s) for s in raw]
    return [load_skill_from_dict(raw)]
