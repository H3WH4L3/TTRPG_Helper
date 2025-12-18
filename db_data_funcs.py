import sqlite3
from db import get_connection


# Helpfull func to take classes id
def select_class_id(cls):
    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute(
            "SELECT id FROM classes WHERE name_ru=?",
            (cls,),
        )
        return dict(cursor.fetchone())["id"]


# CLASSES
def show_all_classes():
    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute("SELECT name_ru FROM classes;")
        return [dict(i) for i in cursor.fetchall()]


def show_info_classes(cls):
    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute(
            "SELECT name_ru, desc_ru, hp_formula FROM classes WHERE name_ru=?;", (cls,)
        )
        return dict(cursor.fetchone())


# region ITEMS
def show_all_items():
    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute("SELECT DISTINCT name_ru FROM items;")
        return [dict(i) for i in cursor.fetchall()]


def show_info_items(item):
    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute(
            """
            SELECT name_ru, effect, counts, cost, category
            FROM items
            WHERE name_ru=?
            """,
            (item,),
        )
        return dict(cursor.fetchone())


# endregion


# region ARMORS
def show_all_armors():
    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute("SELECT DISTINCT name_ru FROM armors;")
        return [dict(i) for i in cursor.fetchall()]


def show_info_armor(armor):
    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute(
            """
            SELECT name_ru, armor_level, effect
            FROM armors
            WHERE name_ru=?
            """,
            (armor,),
        )
        return dict(cursor.fetchone())


# endregion


# region WEAPONS
def show_all_weapons():
    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute("SELECT DISTINCT name_ru FROM weapons;")
        return [dict(i) for i in cursor.fetchall()]


def show_info_weapons(weapon):
    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute(
            """
            SELECT name_ru, damage, effect, ammo
            FROM weapons
            WHERE name_ru=?
            """,
            (weapon,),
        )
        return dict(cursor.fetchone())


# endregion


# region SKILLS
def show_all_skills():
    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute("SELECT DISTINCT name_ru FROM skills;")
        return [dict(i) for i in cursor.fetchall()]


def show_info_skill(skill):
    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute(
            """
            SELECT name_ru, desc_ru
            FROM skills
            WHERE name_ru=?
            """,
            (skill,),
        )
        return dict(cursor.fetchone())


# endregion


# region BONUSES
def show_all_bonuses(cls):
    cls_id = select_class_id(cls)

    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute(
            "SELECT bonuses_id FROM class_bonuses WHERE class_id=?",
            (cls_id,),
        )
        bonus_ids = [dict(i)["bonuses_id"] for i in cursor.fetchall()]
        placeholders = ",".join(["?"] * len(bonus_ids))

        cursor.execute(
            f"SELECT name_ru FROM bonuses WHERE id IN ({placeholders})",
            tuple(bonus_ids),
        )
        return [row["name_ru"] for row in cursor.fetchall()]


def show_info_bonuses(bonus):
    with get_connection() as con:
        cursror = con.cursor()
        cursror.execute(
            "SELECT name_ru, desc_ru FROM bonuses WHERE name_ru=?",
            (bonus,),
        )
        return dict(cursror.fetchone())


# endregion


# region MEMORIES
def show_all_memories(cls):
    cls_id = select_class_id(cls)

    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute(
            "SELECT memories_id FROM class_memories WHERE class_id=?",
            (cls_id,),
        )
        memories_ids = [dict(i)["memories_id"] for i in cursor.fetchall()]
        placeholders = ",".join(["?"] * len(memories_ids))

        cursor.execute(
            f"SELECT name_ru FROM memories WHERE id IN ({placeholders})",
            tuple(memories_ids),
        )
        return [row["name_ru"] for row in cursor.fetchall()]


def show_info_memories(memorie):
    with get_connection() as con:
        cursror = con.cursor()
        cursror.execute(
            "SELECT name_ru, desc_ru FROM memories WHERE name_ru=?",
            (memorie,),
        )
        return dict(cursror.fetchone())


# endregion


# region NARRATIVE
def show_all_narratives(ctg):
    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute(
            "SELECT text_ru FROM narrative WHERE category=?",
            (ctg,),
        )

        return [row["text_ru"] for row in cursor.fetchall()]


# endregion
