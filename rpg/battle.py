"""Automatic turn-based battle engine."""

from typing import Any, Dict, List, Optional

from .models import Character, Effect, StatusEffect


_MAX_TURNS = 100  # safety cap to prevent infinite loops


class Battle:
    """Runs a single battle between *player* and a list of *enemies*.

    Combat is fully automatic:
    1. Each turn, all living characters act in descending speed order.
    2. Each character executes up to *action_count* skills from their skill
       list (starting from index 0 each turn).
    3. Each skill's effects are resolved in order:
       - ``"damage"``  → deal ``atk * coefficient`` HP damage to the target.
       - ``"heal"``    → restore ``rcv * coefficient`` HP to the actor.
       - ``"status"``  → apply a named status effect (magnitude = coefficient,
                         default duration = 3 turns) to the target.
    4. At the end of every turn, status-effect durations are decremented and
       expired effects are removed.
    5. The battle ends when either the player or all enemies are defeated, or
       after :data:`_MAX_TURNS` turns (draw).
    """

    def __init__(self, player: Character, enemies: List[Character]) -> None:
        self.player = player
        self.enemies = enemies
        self._turn_logs: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _living_enemies(self) -> List[Character]:
        return [e for e in self.enemies if e.is_alive()]

    def _is_over(self) -> bool:
        return not self.player.is_alive() or not self._living_enemies()

    def _get_target(self, actor: Character) -> Optional[Character]:
        """Return the first valid target for *actor*."""
        if actor is self.player:
            living = self._living_enemies()
            return living[0] if living else None
        return self.player if self.player.is_alive() else None

    def _apply_effect(
        self,
        actor: Character,
        effect: Effect,
        offensive_target: Character,
    ) -> Dict[str, Any]:
        """Resolve a single effect and return a result dict."""
        result: Dict[str, Any] = {
            "effect_type": effect.effect_type,
            "coefficient": effect.coefficient,
        }

        if effect.effect_type == "damage":
            amount = int(actor.atk * effect.coefficient)
            actual = offensive_target.take_damage(amount)
            result["target"] = offensive_target.name
            result["damage"] = actual

        elif effect.effect_type == "heal":
            amount = int(actor.rcv * effect.coefficient)
            actual = actor.heal_hp(amount)
            result["target"] = actor.name
            result["healed"] = actual

        elif effect.effect_type == "status":
            se = StatusEffect(
                name=effect.status_name or "unknown",
                magnitude=effect.coefficient,
                duration=3,
            )
            offensive_target.apply_status(se)
            result["target"] = offensive_target.name
            result["status_name"] = se.name
            result["magnitude"] = se.magnitude

        return result

    def _execute_skill(self, actor: Character, skill_index: int) -> Dict[str, Any]:
        """Execute one skill and return its action log entry."""
        skill = actor.skills[skill_index]
        target = self._get_target(actor)
        effects_log: List[Dict[str, Any]] = []

        for effect in skill.effects:
            if not actor.is_alive():
                break
            if effect.effect_type in ("damage", "status"):
                # Re-query target in case the previous effect killed it
                if target is None or not target.is_alive():
                    target = self._get_target(actor)
                if target is None:
                    break
                effects_log.append(self._apply_effect(actor, effect, target))
            else:  # "heal" – always targets self
                effects_log.append(self._apply_effect(actor, effect, actor))

        return {
            "actor": actor.name,
            "skill": skill.to_dict(),
            "effects": effects_log,
        }

    def _snapshot(self) -> List[Dict[str, Any]]:
        """Snapshot HP/SP/status of all characters."""
        chars = [self.player] + self.enemies
        return [
            {
                "name": c.name,
                "hp": c.hp,
                "max_hp": c.max_hp,
                "sp": c.sp,
                "max_sp": c.max_sp,
                "status_effects": [se.to_dict() for se in c.status_effects],
            }
            for c in chars
        ]

    def _tick_status_effects(self) -> None:
        """Decrement duration of all active status effects; remove expired ones."""
        for char in [self.player] + self.enemies:
            char.status_effects = [se for se in char.status_effects if se.duration > 0]
            for se in char.status_effects:
                se.duration -= 1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        """Execute the battle and return the full log as a JSON-serialisable dict."""
        turn_number = 0

        while not self._is_over() and turn_number < _MAX_TURNS:
            turn_number += 1
            turn_log: Dict[str, Any] = {
                "turn": turn_number,
                "status_at_start": self._snapshot(),
                "actions": [],
            }

            # Characters act in descending speed order
            acting_order = sorted(
                [c for c in [self.player] + self.enemies if c.is_alive()],
                key=lambda c: c.speed,
                reverse=True,
            )

            for actor in acting_order:
                if not actor.is_alive() or self._is_over():
                    break
                num_actions = min(actor.action_count, len(actor.skills))
                for i in range(num_actions):
                    if not actor.is_alive() or self._is_over():
                        break
                    turn_log["actions"].append(self._execute_skill(actor, i))

            self._tick_status_effects()
            self._turn_logs.append(turn_log)

        # Determine outcome
        if self.player.is_alive() and not self._living_enemies():
            result = "player_win"
        elif not self.player.is_alive():
            result = "player_lose"
        else:
            result = "draw"

        return {"result": result, "turns": self._turn_logs}
