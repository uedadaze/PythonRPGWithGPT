"""Tests for rpg.models."""

import pytest
from rpg.models import Character, Effect, Skill, StatusEffect


# ---------------------------------------------------------------------------
# Effect
# ---------------------------------------------------------------------------


def test_effect_to_dict_damage():
    e = Effect(effect_type="damage", coefficient=1.5)
    d = e.to_dict()
    assert d == {"effect_type": "damage", "coefficient": 1.5}
    assert "status_name" not in d


def test_effect_to_dict_status():
    e = Effect(effect_type="status", coefficient=0.5, status_name="poison")
    d = e.to_dict()
    assert d["status_name"] == "poison"


# ---------------------------------------------------------------------------
# Skill
# ---------------------------------------------------------------------------


def test_skill_to_dict():
    skill = Skill(name="Slash", effects=[Effect("damage", 1.0)])
    d = skill.to_dict()
    assert d["name"] == "Slash"
    assert len(d["effects"]) == 1


# ---------------------------------------------------------------------------
# Character – basic construction
# ---------------------------------------------------------------------------


def make_char(**kwargs) -> Character:
    defaults = dict(
        name="Test",
        max_hp=100,
        max_sp=50,
        atk=20,
        rcv=15,
        speed=10,
        action_count=1,
    )
    defaults.update(kwargs)
    return Character(**defaults)


def test_character_initial_hp_equals_max_hp():
    c = make_char(max_hp=80)
    assert c.hp == 80


def test_character_is_alive():
    c = make_char()
    assert c.is_alive()
    c.hp = 0
    assert not c.is_alive()


# ---------------------------------------------------------------------------
# Character.take_damage
# ---------------------------------------------------------------------------


def test_take_damage_normal():
    c = make_char(max_hp=100)
    actual = c.take_damage(30)
    assert actual == 30
    assert c.hp == 70


def test_take_damage_cannot_go_below_zero():
    c = make_char(max_hp=100)
    c.hp = 20
    actual = c.take_damage(50)
    assert actual == 20
    assert c.hp == 0


def test_take_damage_negative_clamped_to_zero():
    c = make_char(max_hp=100)
    actual = c.take_damage(-10)
    assert actual == 0
    assert c.hp == 100


# ---------------------------------------------------------------------------
# Character.heal_hp
# ---------------------------------------------------------------------------


def test_heal_hp_normal():
    c = make_char(max_hp=100)
    c.hp = 60
    actual = c.heal_hp(20)
    assert actual == 20
    assert c.hp == 80


def test_heal_hp_cannot_exceed_max():
    c = make_char(max_hp=100)
    c.hp = 90
    actual = c.heal_hp(50)
    assert actual == 10
    assert c.hp == 100


def test_heal_hp_negative_clamped_to_zero():
    c = make_char(max_hp=100)
    c.hp = 50
    actual = c.heal_hp(-5)
    assert actual == 0
    assert c.hp == 50


# ---------------------------------------------------------------------------
# Character.apply_status
# ---------------------------------------------------------------------------


def test_apply_status_adds_new():
    c = make_char()
    se = StatusEffect(name="poison", magnitude=0.5, duration=3)
    c.apply_status(se)
    assert len(c.status_effects) == 1
    assert c.status_effects[0].name == "poison"


def test_apply_status_refreshes_existing():
    c = make_char()
    c.apply_status(StatusEffect(name="poison", magnitude=0.3, duration=2))
    c.apply_status(StatusEffect(name="poison", magnitude=0.7, duration=5))
    assert len(c.status_effects) == 1
    assert c.status_effects[0].magnitude == 0.7
    assert c.status_effects[0].duration == 5


def test_apply_status_different_effects_stack():
    c = make_char()
    c.apply_status(StatusEffect(name="poison", magnitude=0.5, duration=3))
    c.apply_status(StatusEffect(name="burn", magnitude=1.0, duration=2))
    assert len(c.status_effects) == 2


# ---------------------------------------------------------------------------
# Character.to_dict
# ---------------------------------------------------------------------------


def test_character_to_dict_keys():
    c = make_char()
    d = c.to_dict()
    for key in ("name", "hp", "max_hp", "sp", "max_sp", "atk", "rcv", "speed",
                "action_count", "skills", "status_effects"):
        assert key in d
