"""Tests for rpg.battle and rpg.loader."""

import json
import os
import tempfile

import pytest

from rpg.battle import Battle
from rpg.loader import (
    load_character_from_dict,
    load_characters_from_file,
    load_effect_from_dict,
    load_skill_from_dict,
    load_skills_from_file,
)
from rpg.models import Character, Effect, Skill, StatusEffect


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_char(name="Hero", max_hp=100, atk=20, rcv=15, speed=10,
              action_count=1, skills=None) -> Character:
    return Character(
        name=name,
        max_hp=max_hp,
        max_sp=50,
        atk=atk,
        rcv=rcv,
        speed=speed,
        action_count=action_count,
        skills=skills or [],
    )


def damage_skill(name="Attack", coefficient=1.0) -> Skill:
    return Skill(name=name, effects=[Effect("damage", coefficient)])


def heal_skill(name="Heal", coefficient=1.0) -> Skill:
    return Skill(name=name, effects=[Effect("heal", coefficient)])


def status_skill(name="Poison", coefficient=0.5, status_name="poison") -> Skill:
    return Skill(name=name, effects=[Effect("status", coefficient, status_name)])


# ---------------------------------------------------------------------------
# Loader – primitives
# ---------------------------------------------------------------------------


def test_load_effect_from_dict_damage():
    e = load_effect_from_dict({"effect_type": "damage", "coefficient": 1.5})
    assert e.effect_type == "damage"
    assert e.coefficient == 1.5
    assert e.status_name is None


def test_load_effect_from_dict_status():
    e = load_effect_from_dict(
        {"effect_type": "status", "coefficient": 0.5, "status_name": "burn"}
    )
    assert e.status_name == "burn"


def test_load_skill_from_dict():
    s = load_skill_from_dict({
        "name": "Slash",
        "effects": [{"effect_type": "damage", "coefficient": 1.2}],
    })
    assert s.name == "Slash"
    assert len(s.effects) == 1


def test_load_character_from_dict():
    c = load_character_from_dict({
        "name": "Goblin",
        "max_hp": 50, "max_sp": 20,
        "atk": 12, "rcv": 8, "speed": 8, "action_count": 1,
        "skills": [], "status_effects": [],
    })
    assert c.name == "Goblin"
    assert c.hp == 50


def test_load_character_from_dict_custom_hp():
    c = load_character_from_dict({
        "name": "Goblin", "max_hp": 50, "max_sp": 20, "hp": 30,
        "atk": 12, "rcv": 8, "speed": 8, "action_count": 1,
    })
    assert c.hp == 30


# ---------------------------------------------------------------------------
# Loader – file I/O
# ---------------------------------------------------------------------------


def _write_json(obj) -> str:
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    with open(path, "w") as fh:
        json.dump(obj, fh)
    return path


def test_load_characters_from_file_list():
    data = [
        {"name": "A", "max_hp": 10, "max_sp": 5, "atk": 1, "rcv": 1,
         "speed": 1, "action_count": 1},
        {"name": "B", "max_hp": 20, "max_sp": 5, "atk": 2, "rcv": 2,
         "speed": 2, "action_count": 1},
    ]
    path = _write_json(data)
    try:
        chars = load_characters_from_file(path)
        assert len(chars) == 2
        assert chars[0].name == "A"
    finally:
        os.unlink(path)


def test_load_skills_from_file():
    data = [
        {"name": "S1", "effects": [{"effect_type": "damage", "coefficient": 1.0}]},
        {"name": "S2", "effects": [{"effect_type": "heal", "coefficient": 0.5}]},
    ]
    path = _write_json(data)
    try:
        skills = load_skills_from_file(path)
        assert len(skills) == 2
        assert skills[1].name == "S2"
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Battle – outcome
# ---------------------------------------------------------------------------


def test_player_wins():
    """Player with high ATK should defeat a weak enemy quickly."""
    player = make_char("Hero", max_hp=200, atk=100, speed=10,
                       skills=[damage_skill()])
    enemy = make_char("Slime", max_hp=30, atk=5, speed=1, skills=[damage_skill()])
    result = Battle(player, [enemy]).run()
    assert result["result"] == "player_win"


def test_player_loses():
    """A player with no skills against a powerful enemy should lose."""
    player = make_char("Hero", max_hp=10, atk=1, speed=1, skills=[damage_skill(coefficient=0.01)])
    enemy = make_char("Dragon", max_hp=500, atk=200, speed=20, skills=[damage_skill()])
    result = Battle(player, [enemy]).run()
    assert result["result"] == "player_lose"


def test_battle_has_turns():
    player = make_char("Hero", max_hp=100, atk=20, speed=10, skills=[damage_skill()])
    enemy = make_char("Slime", max_hp=40, atk=8, speed=5, skills=[damage_skill()])
    result = Battle(player, [enemy]).run()
    assert len(result["turns"]) >= 1


def test_each_turn_has_status_at_start():
    player = make_char("Hero", max_hp=100, atk=20, speed=10, skills=[damage_skill()])
    enemy = make_char("Slime", max_hp=40, atk=8, speed=5, skills=[damage_skill()])
    result = Battle(player, [enemy]).run()
    for turn in result["turns"]:
        assert "status_at_start" in turn
        assert "actions" in turn
        assert "turn" in turn


# ---------------------------------------------------------------------------
# Battle – damage effect
# ---------------------------------------------------------------------------


def test_damage_reduces_enemy_hp():
    player = make_char("Hero", max_hp=200, atk=20, speed=10, skills=[damage_skill(coefficient=1.0)])
    enemy = make_char("Slime", max_hp=100, atk=1, speed=1, skills=[damage_skill(coefficient=0.01)])
    result = Battle(player, [enemy]).run()
    # Find first damage action by Hero
    actions = result["turns"][0]["actions"]
    hero_action = next(a for a in actions if a["actor"] == "Hero")
    dmg_effect = next(e for e in hero_action["effects"] if e["effect_type"] == "damage")
    assert dmg_effect["damage"] == 20  # 20 atk * 1.0 coefficient


# ---------------------------------------------------------------------------
# Battle – heal effect
# ---------------------------------------------------------------------------


def test_heal_restores_hp():
    player = make_char("Hero", max_hp=100, rcv=15, atk=1, speed=10, action_count=1,
                       skills=[heal_skill(coefficient=1.0)])
    enemy = make_char("Enemy", max_hp=500, atk=10, speed=5, skills=[damage_skill()])
    # Wound player first
    player.hp = 50
    result = Battle(player, [enemy]).run()
    # Hero heals first (higher speed); check heal effect exists
    actions = result["turns"][0]["actions"]
    hero_action = next(a for a in actions if a["actor"] == "Hero")
    heal_effect = next(e for e in hero_action["effects"] if e["effect_type"] == "heal")
    assert heal_effect["healed"] == 15  # rcv=15 * 1.0


# ---------------------------------------------------------------------------
# Battle – status effect
# ---------------------------------------------------------------------------


def test_status_applied_to_enemy():
    player = make_char("Hero", max_hp=200, atk=20, speed=10,
                       skills=[status_skill(coefficient=0.5, status_name="poison")])
    enemy = make_char("Slime", max_hp=200, atk=1, speed=1, skills=[damage_skill()])
    result = Battle(player, [enemy]).run()
    actions = result["turns"][0]["actions"]
    hero_action = next(a for a in actions if a["actor"] == "Hero")
    status_effect = next(e for e in hero_action["effects"] if e["effect_type"] == "status")
    assert status_effect["status_name"] == "poison"
    assert status_effect["magnitude"] == 0.5


# ---------------------------------------------------------------------------
# Battle – multiple enemies
# ---------------------------------------------------------------------------


def test_player_defeats_multiple_enemies():
    player = make_char("Hero", max_hp=500, atk=100, speed=20, action_count=1,
                       skills=[damage_skill(coefficient=2.0)])
    enemies = [
        make_char("Slime", max_hp=30, atk=5, speed=1, skills=[damage_skill()]),
        make_char("Goblin", max_hp=50, atk=8, speed=2, skills=[damage_skill()]),
    ]
    result = Battle(player, enemies).run()
    assert result["result"] == "player_win"


# ---------------------------------------------------------------------------
# Battle – action_count limits skills used per turn
# ---------------------------------------------------------------------------


def test_action_count_limits_actions():
    """A character with action_count=1 should only use 1 skill per turn."""
    player = make_char("Hero", max_hp=200, atk=10, speed=10, action_count=1,
                       skills=[damage_skill("Atk1"), damage_skill("Atk2")])
    enemy = make_char("Dummy", max_hp=500, atk=1, speed=1, skills=[damage_skill()])
    result = Battle(player, [enemy]).run()
    hero_actions = [a for a in result["turns"][0]["actions"] if a["actor"] == "Hero"]
    assert len(hero_actions) == 1


def test_action_count_two_uses_two_skills():
    player = make_char("Hero", max_hp=200, atk=10, speed=10, action_count=2,
                       skills=[damage_skill("Atk1"), damage_skill("Atk2")])
    enemy = make_char("Dummy", max_hp=500, atk=1, speed=1, skills=[damage_skill()])
    result = Battle(player, [enemy]).run()
    hero_actions = [a for a in result["turns"][0]["actions"] if a["actor"] == "Hero"]
    assert len(hero_actions) == 2


# ---------------------------------------------------------------------------
# Battle – draw after max turns
# ---------------------------------------------------------------------------


def test_draw_when_no_one_dies():
    """Characters that cannot damage each other should reach the turn cap."""
    player = make_char("Hero", max_hp=1000, atk=0, speed=10, action_count=1,
                       skills=[damage_skill(coefficient=0.0)])
    enemy = make_char("Dummy", max_hp=1000, atk=0, speed=1, action_count=1,
                       skills=[damage_skill(coefficient=0.0)])
    result = Battle(player, [enemy]).run()
    assert result["result"] == "draw"
