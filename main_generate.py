import psycopg2
import json
from random import randint, choice
from psycopg2.extras import DictCursor
from dataclasses import dataclass
import re
import operator as op
import os
from dotenv import load_dotenv

load_dotenv()
OPERATORS = {"+": op.add, "-": op.sub, "//": op.floordiv, "*": op.mul}

connection = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
)
cursor = connection.cursor(cursor_factory=DictCursor)


@dataclass
class Character:
    id: str
    name: str
    age: int
    sex: str
    character_class: str
    description: str
    hp: int
    money: int
    signs: int
    skills: dict
    agility: int
    presence: int
    strength: int
    toughness: int
    bonus: str
    terrible_trait: str
    injurie: str
    bad_habit: str
    dangerous_past: str
    secret_quest: str
    memorie: str
    armor: dict
    weapon: dict
    items: list


class MBCharacter:
    def __init__(self):
        self.character = None

    @staticmethod
    def roll_dice(string):
        pattern = r"(?:(\d*)d)?(\d+)([+\-*])?(\d+)?"
        match = re.fullmatch(pattern, string)
        if match:
            count, value, operator, bonus = match.groups()
            count = int(count) if count else 1
            value = int(value)
            operator = OPERATORS.get(operator, op.add)
            bonus = int(bonus) if bonus else 0
            roll = sum([randint(1, value) for _ in range(count)])
            return operator(roll, bonus)

    def generate(self):
        data = {}

        # Basic
        data["age"] = randint(18, 60)
        data["sex"] = choice(["Мужчина", "Женщина"])

        # Choose the class
        cursor.execute("SELECT * FROM classes ORDER BY random() LIMIT 1;")
        ch_cls = cursor.fetchone()
        class_id = ch_cls["id"]

        data["id"] = ch_cls["slug"]
        data["character_class"] = ch_cls["name_ru"]
        data["description"] = ch_cls["desc_ru"]
        data["hp"] = self.roll_dice(ch_cls["hp_formula"])
        data["money"] = self.roll_dice(ch_cls["money_formula"])
        data["signs"] = self.roll_dice(ch_cls["signs_formula"])

        # Abilities
        data["agility"] = self.roll_dice(ch_cls["agility_formula"])
        data["presence"] = self.roll_dice(ch_cls["presence_formula"])
        data["strength"] = self.roll_dice(ch_cls["strength_formula"])
        data["toughness"] = self.roll_dice(ch_cls["toughness_formula"])

        # Bonus
        data["bonus"] = {"type": ch_cls["bonus_type"]}

        cursor.execute(
            "SELECT bonuses_id FROM class_bonuses WHERE class_id = %s ORDER BY random() LIMIT 1;",
            (class_id,),
        )
        ch_bonus = cursor.fetchone()[0]

        cursor.execute("SELECT * FROM bonuses WHERE id = %s;", (ch_bonus,))
        ch_bonus = cursor.fetchone()
        data["bonus"]["text"] = f"{ch_bonus["name_ru"]} : {ch_bonus["desc_ru"]}"

        # Skills
        cursor.execute(
            "SELECT skills_id FROM class_skills WHERE class_id = %s;", (class_id,)
        )
        ch_skills = tuple(element[0] for element in cursor.fetchall())

        cursor.execute(
            "SELECT name_ru, desc_ru FROM skills WHERE id IN %s;", (ch_skills,)
        )
        ch_skills = cursor.fetchall()
        ch_skills = {e["name_ru"]: e["desc_ru"] for e in ch_skills}
        data["skills"] = ch_skills

        # Narrative
        cursor.execute(
            """SELECT n.*
            FROM (SELECT DISTINCT category FROM narrative) c
            CROSS JOIN LATERAL (
            SELECT *
            FROM narrative n
            WHERE n.category = c.category
            ORDER BY random()
            LIMIT 1
            ) n
            ORDER BY c.category;
            """
        )
        ch_narrative = {e[2]: e[3] for e in cursor.fetchall()}
        for key, value in ch_narrative.items():
            data[key] = value

        # Memories
        cursor.execute(
            "SELECT memories_id FROM class_memories WHERE class_id = %s ORDER BY random() LIMIT 1;",
            (class_id,),
        )
        ch_memorie = cursor.fetchone()[0]
        cursor.execute(
            "SELECT * FROM memories WHERE id = %s;",
            (ch_memorie,),
        )
        ch_memorie = cursor.fetchone()
        data["memorie"] = f"{ch_cls["memorie_type"]} {ch_memorie["desc_ru"]}"
        # Armor
        if ch_cls["armor_formula"] is None:
            data["armor"] = {"name": "Нет брони", "level": 0, "effect": None}
        else:
            cursor.execute(
                "SELECT * FROM armors WHERE id = %s;",
                (randint(1, self.roll_dice(ch_cls["armor_formula"])),),
            )
            ch_armor = cursor.fetchone()
            data["armor"] = {
                "name": ch_armor["name_ru"],
                "level": ch_armor["armor_level"],
                "effect": ch_armor["effect"],
            }

        # Weapon
        if ch_cls["weapon_formula"] is None:
            data["weapon"] = {
                "name": "Невооруженный",
                "damage": "d1",
                "effect": None,
                "ammo": None,
            }
        else:
            cursor.execute(
                "SELECT * FROM weapons WHERE id = %s;",
                (randint(1, self.roll_dice(ch_cls["weapon_formula"])),),
            )
            ch_weapon = cursor.fetchone()
            data["weapon"] = {
                "name": ch_weapon["name_ru"],
                "damage": ch_weapon["damage"],
                "effect": ch_weapon["effect"],
                "ammo": (
                    data["presence"] + int(ch_weapon["ammo"].split()[2])
                    if ch_weapon["ammo"]
                    else None
                ),
            }

        # Items
        data["items"] = {}
        for element in ("first", "second", "third"):
            cursor.execute(
                "SELECT * FROM items WHERE category = %s ORDER BY random() LIMIT 1;",
                (element,),
            )
            ch_items = cursor.fetchone()
            data["items"][ch_items["name_ru"]] = {
                "effect": ch_items["effect"],
                "counts": ch_items["counts"],
                "cost": ch_items["cost"],
            }

        self.character = Character(**data)
