"""Entry point for the Python RPG battle system.

Usage examples
--------------
Show enemy info before battle::

    python main.py --output enemy_info

Run a battle using a player skill list from a JSON file::

    python main.py --skills data/example_skills.json

Specify custom player / enemy files::

    python main.py --player data/player.json --enemies data/enemies.json \\
                   --skills data/example_skills.json
"""

import argparse
import json
from pathlib import Path

from rpg.battle import Battle
from rpg.loader import load_characters_from_file, load_skills_from_file

_DATA_DIR = Path(__file__).parent / "data"


def _enemy_info(enemies: list) -> list:
    """Return a JSON-serialisable list of enemy stats (pre-battle snapshot)."""
    return [
        {
            "name": e.name,
            "max_hp": e.max_hp,
            "max_sp": e.max_sp,
            "atk": e.atk,
            "rcv": e.rcv,
            "speed": e.speed,
            "action_count": e.action_count,
            "skills": [s.to_dict() for s in e.skills],
        }
        for e in enemies
    ]


def main() -> None:
    # こういう形で実行時引数を1つずつ指定できるようだ
    parser = argparse.ArgumentParser(description="Python RPG Battle System")
    parser.add_argument(
        "--skills", "-s",
        metavar="FILE",
        help="JSON file containing the player's skill list",
    )
    parser.add_argument(
        "--output", "-o",
        choices=["enemy_info", "battle"],
        default="battle",
        help="'enemy_info' outputs pre-battle enemy stats; 'battle' runs the battle (default)",
    )
    parser.add_argument(
        "--player", "-p",
        metavar="FILE",
        default=str(_DATA_DIR / "player.json"),
        help="JSON file for the player character (default: data/player.json)",
    )
    parser.add_argument(
        "--enemies", "-e",
        metavar="FILE",
        default=str(_DATA_DIR / "enemies.json"),
        help="JSON file for the enemy roster (default: data/enemies.json)",
    )
    args = parser.parse_args()
    # --を取っ払ったものをattributeとして取得可能
    player = load_characters_from_file(args.player)[0]
    enemies = load_characters_from_file(args.enemies)
    # 出力としてenemy_infoを指定した場合敵の情報をJSON形式で出力する
    if args.output == "enemy_info":
        print(json.dumps(_enemy_info(enemies), ensure_ascii=False, indent=2))
        return

    if args.skills:
        player.skills = load_skills_from_file(args.skills)

    battle = Battle(player, enemies)
    result = battle.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
