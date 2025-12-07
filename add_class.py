import re
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, g
from dotenv import load_dotenv
import os

load_dotenv()


app = Flask(__name__)
connection = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
)
cursor = connection.cursor()

VALIDATION_TEXT = {
    "slug": "Только латиница, нижний регистр, слова через _",
    "name": "Только кирриллица, слова разделяются пробелом, никаких символов",
    "desc": "Только кориллица, допускается любой свободный форма, в конце точка",
    "formula": "Только формат вида XdY/XdY±Z (3d6/3d6±2)",
    "dublicate": "Такой id уже есть в базе!",
}


def validate_form(slug=None, name=None, describe=None, formula=None):
    if slug:
        return re.fullmatch(r"^[a-z]+(?:_[a-z]+)*$", slug)
    if name:
        return re.fullmatch(r"^[А-ЯЁ][а-яё]+(?: [А-ЯЁа-яё]+)*$", name)
    if describe:
        return re.fullmatch(r"^[А-ЯЁ][А-ЯЁа-яё0-9 ,:;()\-!?]*\.$", describe)
    if formula:
        return re.fullmatch(r"(?:(\d*)d)?(\d+)([+\-])?(\d+)?", formula)


def execute_param(result: dict) -> tuple:
    keys = ", ".join(result.keys())
    placeholders = ", ".join(["%s"] * len(result))
    return (keys, placeholders)


narrative_category_translator = {
    "bad_habit": "Вредная привычка",
    "terrible_trait": "Ужасная черта характера",
    "dangerous_past": "Опасное прошлое",
    "injurie": "Травма",
    "secret_quest": "Секретный твист",
    "name": "Имя",
}


# MAIN PAGE
@app.route("/")
def index():
    return render_template("index.html")


# ADD NEW CLASS
@app.route("/add_class", methods=["POST", "GET"])
def add_class():
    if request.method == "GET":
        return render_template("add_class.html", form={}, errors={})

    errors = {}
    new_class = {}

    # Taking all values
    new_class["slug"] = request.form.get("slug", "").strip()
    new_class["name_ru"] = request.form.get("name_ru", "").strip()
    new_class["desc_ru"] = request.form.get("desc_ru", "").strip()
    new_class["hp_formula"] = request.form.get("hp_formula", "").strip()
    new_class["money_formula"] = request.form.get("money_formula", "").strip()
    new_class["signs_formula"] = request.form.get("signs_formula", "").strip()
    new_class["agility_formula"] = request.form.get("agility_formula", "").strip()
    new_class["presence_formula"] = request.form.get("presence_formula", "").strip()
    new_class["strength_formula"] = request.form.get("strength_formula", "").strip()
    new_class["toughness_formula"] = request.form.get("toughness_formula", "").strip()
    new_class["weapon_formula"] = request.form.get("weapon_formula", "").strip()
    new_class["armor_formula"] = request.form.get("armor_formula", "").strip()

    # Checking for errors
    cursor.execute("SELECT slug FROM classes")
    slugs_classes = [i[0] for i in cursor.fetchall()]
    if not validate_form(slug=new_class["slug"]) and "1" in new_class["slug"]:
        errors["slug"] = VALIDATION_TEXT["slug"]
    if new_class["slug"] in slugs_classes:
        errors["slug"] = VALIDATION_TEXT["dublicate"]
    if not validate_form(name=new_class["name_ru"]):
        errors["name_ru"] = VALIDATION_TEXT["name"]
    if not validate_form(describe=new_class["desc_ru"]):
        errors["desc_ru"] = VALIDATION_TEXT["desc"]
    for key, value in new_class.items():
        if key.endswith("formula"):
            if not validate_form(formula=value):
                errors[key] = VALIDATION_TEXT["formula"]

    # If there any errors -> Render template with error messages
    if errors:
        return render_template("add_class.html", errors=errors, form=new_class)

    keys, placeholders = execute_param(new_class)
    cursor.execute(
        f"""
                INSERT INTO classes
                (
                {keys}
                )
                VALUES ({placeholders})
                """,
        tuple(new_class.values()),
    )
    connection.commit()
    return redirect(url_for("index"))


# ADD NEW SKILL
@app.route("/add_skill", methods=["POST", "GET"])
def add_skill():
    cursor.execute("SELECT id, name_ru FROM classes")
    classes = cursor.fetchall()

    if request.method == "GET":
        empty_skill = {"slug": "", "name_ru": "", "desc_ru": ""}
        return render_template(
            "add_skill.html",
            form=[empty_skill],
            errors=[{}],
            classes=classes,
            selected_class_id="",
        )

    # Extracting all values from form
    class_id = request.form.get("class_id", "").strip()
    slugs = request.form.getlist("slug[]")
    names = request.form.getlist("name_ru[]")
    descs = request.form.getlist("desc_ru[]")

    new_skill = []
    errors = []

    for i in range(len(slugs)):
        skill_error = {}

        slug = slugs[i].strip()
        name = names[i].strip()
        desc = descs[i].strip()

        if not validate_form(slug=slug):
            skill_error["slug"] = VALIDATION_TEXT["slug"]

        cursor.execute("SELECT slug FROM skills")
        slugs_skills = [i[0] for i in cursor.fetchall()]
        if slug in slugs_skills:
            skill_error["slug"] = VALIDATION_TEXT["dublicate"]

        if not validate_form(name=name):
            skill_error["name_ru"] = VALIDATION_TEXT["name"]

        if not validate_form(describe=desc):
            skill_error["desc_ru"] = VALIDATION_TEXT["desc"]

        errors.append(skill_error)

        new_skill.append({"slug": slug, "name_ru": name, "desc_ru": desc})

    if any(errors):
        return render_template(
            "add_skill.html",
            form=new_skill,
            errors=errors,
            classes=classes,
            selected_class_id=class_id,
        )

    for skill in new_skill:
        keys, placeholder = execute_param(skill)

        # Adding Skill to main table
        cursor.execute(
            f"INSERT INTO skills ({keys}) VALUES ({placeholder}) RETURNING id;",
            tuple(skill.values()),
        )
        skill_id = cursor.fetchone()[0]

        # Adding link between ids
        cursor.execute(
            "INSERT INTO class_skills (class_id, skill_id) VALUES (%s, %s);",
            (int(class_id), skill_id),
        )

    connection.commit()
    return redirect(url_for("index"))


# ADD NEW BONUS
@app.route("/add_bonus", methods=["POST", "GET"])
def add_bonus():
    cursor.execute("SELECT id, name_ru FROM classes")
    classes = cursor.fetchall()

    if request.method == "GET":
        empty_bonus = {"slug": "", "name_ru": "", "desc_ru": ""}
        return render_template(
            "add_bonus.html",
            form=[empty_bonus],
            errors=[{}],
            classes=classes,
            selected_class_id="",
            bonus_type="",
            type_error="",
        )

    class_id = request.form.get("class_id", "").strip()
    bonus_type = request.form.get("bonus_type").strip()

    if not validate_form(describe=bonus_type):
        type_error = VALIDATION_TEXT["desc"]
    else:
        type_error = ""

    slugs = request.form.getlist("slug[]")
    names = request.form.getlist("name_ru[]")
    descs = request.form.getlist("desc_ru[]")

    new_bonus = []
    errors = []

    for i in range(len(slugs)):
        bonus_error = {}

        slug = slugs[i].strip()
        name = names[i].strip()
        desc = descs[i].strip()

        if not validate_form(slug=slug):
            bonus_error["slug"] = VALIDATION_TEXT["slug"]

        cursor.execute("SELECT slug FROM bonuses")
        slugs_bonuses = [i[0] for i in cursor.fetchall()]
        if slug in slugs_bonuses:
            bonus_error["slug"] = VALIDATION_TEXT["dublicate"]

        if not validate_form(name=name):
            bonus_error["name_ru"] = VALIDATION_TEXT["name"]

        if not validate_form(describe=desc):
            bonus_error["desc_ru"] = VALIDATION_TEXT["desc"]

        errors.append(bonus_error)

        new_bonus.append({"slug": slug, "name_ru": name, "desc_ru": desc})
    if any(errors) or type_error:
        return render_template(
            "add_bonus.html",
            form=new_bonus,
            errors=errors,
            classes=classes,
            selected_class_id=class_id,
            bonus_type=bonus_type,
            type_error=type_error,
        )

    # Добавляем в базу
    cursor.execute(
        "UPDATE classes SET bonus_type=%s WHERE id=%s",
        (bonus_type, int(class_id)),
    )

    for bonus in new_bonus:
        keys, placeholder = execute_param(bonus)
        # Добавляем бонус
        cursor.execute(
            f"INSERT INTO bonuses ({keys}) VALUES ({placeholder}) RETURNING id;",
            tuple(bonus.values()),
        )
        bonus_id = cursor.fetchone()[0]

        cursor.execute(
            "INSERT INTO class_bonuses (class_id, bonus_id) VALUES (%s, %s);",
            (int(class_id), bonus_id),
        )
    connection.commit()
    return redirect(url_for("index"))


# ADD NEW MEMORIE
@app.route("/add_memorie", methods=["POST", "GET"])
def add_memorie():
    cursor.execute("SELECT id, name_ru FROM classes")
    classes = cursor.fetchall()

    if request.method == "GET":
        empty_memorie = {"slug": "", "name_ru": "", "desc_ru": ""}
        return render_template(
            "add_memorie.html",
            form=[empty_memorie],
            errors=[{}],
            classes=classes,
            selected_class_id="",
            memorie_type="",
            type_error="",
        )

    class_id = request.form.get("class_id", "").strip()
    memorie_type = request.form.get("memorie_type").strip()

    if not validate_form(describe=memorie_type):
        type_error = VALIDATION_TEXT["desc"]
    else:
        type_error = ""

    slugs = request.form.getlist("slug[]")
    names = request.form.getlist("name_ru[]")
    descs = request.form.getlist("desc_ru[]")

    new_memorie = []
    errors = []

    for i in range(len(slugs)):
        memorie_error = {}

        slug = slugs[i].strip()
        name = names[i].strip()
        desc = descs[i].strip()

        if not validate_form(slug=slug):
            memorie_error["slug"] = VALIDATION_TEXT["slug"]

        cursor.execute("SELECT slug FROM memories")
        slugs_memories = [i[0] for i in cursor.fetchall()]
        if slug in slugs_memories:
            memorie_error["slug"] = VALIDATION_TEXT["dublicate"]

        if not validate_form(name=name):
            memorie_error["name_ru"] = VALIDATION_TEXT["name"]

        if not validate_form(describe=desc):
            memorie_error["desc_ru"] = VALIDATION_TEXT["desc"]

        errors.append(memorie_error)

        new_memorie.append({"slug": slug, "name_ru": name, "desc_ru": desc})

    if any(errors) or type_error:
        return render_template(
            "add_memorie.html",
            form=new_memorie,
            errors=errors,
            classes=classes,
            selected_class_id=class_id,
            memorie_type=memorie_type,
            type_error=type_error,
        )

    # Adding new memories
    cursor.execute(
        "UPDATE classes SET memorie_type=%s WHERE id=%s",
        (memorie_type, int(class_id)),
    )

    for memorie in new_memorie:
        keys, placeholder = execute_param(memorie)

        cursor.execute(
            f"INSERT INTO memories ({keys}) VALUES ({placeholder}) RETURNING id;",
            tuple(memorie.values()),
        )
        memorie_id = cursor.fetchone()[0]

        cursor.execute(
            "INSERT INTO class_memories (class_id, memorie_id) VALUES (%s, %s);",
            (int(class_id), memorie_id),
        )
    connection.commit()
    return redirect(url_for("index"))


# ADD NARRATIVE
@app.route("/add_narrative", methods=["POST", "GET"])
def add_narrative():
    cursor.execute("SELECT DISTINCT category FROM narrative;")
    categories = [i[0] for i in cursor.fetchall()]

    categories = [(el, narrative_category_translator[el]) for el in categories]

    if request.method == "GET":
        return render_template(
            "add_narrative.html", form={}, errors={}, categories=categories
        )
    new_narrative = {}
    narrative_errors = {}

    new_narrative["slug"] = request.form.get("slug", "").strip()
    new_narrative["category"] = request.form.get("category", "").strip()
    new_narrative["text_ru"] = request.form.get("text_ru", "").strip()

    cursor.execute(
        "SELECT slug FROM narrative WHERE category=%s", (new_narrative["category"],)
    )
    slugs_narrative = [i[0] for i in cursor.fetchall()]

    if new_narrative["slug"] in slugs_narrative:
        narrative_errors["slug"] = VALIDATION_TEXT["dublicate"]

    if not validate_form(slug=new_narrative["slug"]):
        narrative_errors["slug"] = VALIDATION_TEXT["slug"]

    if not validate_form(name=new_narrative["text_ru"]):
        narrative_errors["text_ru"] = VALIDATION_TEXT["name"]

    if narrative_errors:
        return render_template(
            "add_narrative.html",
            form=new_narrative,
            errors=narrative_errors,
            categories=categories,
            selected_category=new_narrative["category"],
        )

    keys, placeholder = execute_param(new_narrative)

    cursor.execute(
        f"INSERT INTO narrative ({keys}) VALUES ({placeholder});",
        tuple(new_narrative.values()),
    )

    connection.commit()
    return redirect(url_for("index"))


# ADD ARMOR
@app.route("/add_armor", methods=["POST", "GET"])
def add_armor():
    if request.method == "GET":
        return render_template("add_armor.html", form={}, errors={})

    new_armor = {}
    armor_errors = {}

    new_armor["slug"] = request.form.get("slug", "").strip()
    new_armor["name_ru"] = request.form.get("name_ru", "").strip()
    new_armor["armor_level"] = request.form.get("armor_level", "").strip()
    new_armor["effect"] = request.form.get("effect", "").strip()

    cursor.execute("SELECT slug FROM armors;")
    slugs_armor = [i[0] for i in cursor.fetchall()]
    if new_armor["slug"] in slugs_armor:
        armor_errors["slug"] = VALIDATION_TEXT["dublicate"]
    if not validate_form(slug=new_armor["slug"]):
        armor_errors["slug"] = VALIDATION_TEXT["slug"]
    if not validate_form(name=new_armor["name_ru"]):
        armor_errors["name_ru"] = VALIDATION_TEXT["name"]
    if not 0 <= int(new_armor["armor_level"]) <= 10:
        armor_errors["armor_level"] = "Значением может быть только число от 0 до 10"
    if (
        not validate_form(describe=new_armor["effect"])
        and len(new_armor["effect"]) >= 1
    ):
        armor_errors["effect"] = VALIDATION_TEXT["desc"]

    if armor_errors:
        return render_template("add_armor.html", form=new_armor, errors=armor_errors)

    keys, placeholder = execute_param(new_armor)

    cursor.execute(
        f"INSERT INTO armors ({keys}) VALUES ({placeholder});",
        tuple(new_armor.values()),
    )

    connection.commit()
    return redirect(url_for("index"))


# ADD WEAPON
@app.route("/add_weapon", methods=["POST", "GET"])
def add_weapon():
    if request.method == "GET":
        return render_template("add_weapon.html", form={}, errors={})

    new_weapon = {}
    weapon_errors = {}

    new_weapon["slug"] = request.form.get("slug", "").strip()
    new_weapon["name_ru"] = request.form.get("name_ru", "").strip()
    new_weapon["damage"] = request.form.get("damage", "").strip()
    new_weapon["effect"] = request.form.get("effect", "").strip()
    new_weapon["ammo"] = request.form.get("ammo", "").strip()

    cursor.execute("SELECT slug FROM weapons;")
    slugs_weapon = [i[0] for i in cursor.fetchall()]

    if new_weapon["slug"] in slugs_weapon:
        weapon_errors["slug"] = VALIDATION_TEXT["dublicate"]
    if not validate_form(slug=new_weapon["slug"]):
        weapon_errors["slug"] = VALIDATION_TEXT["slug"]
    if not validate_form(name=new_weapon["name_ru"]):
        weapon_errors["name_ru"] = VALIDATION_TEXT["name"]
    if not validate_form(formula=new_weapon["damage"]):
        weapon_errors["damage"] = VALIDATION_TEXT["formula"]
    if (
        not validate_form(describe=new_weapon["effect"])
        and len(new_weapon["effect"]) >= 1
    ):
        weapon_errors["damage"] = VALIDATION_TEXT["desc"] + ". Либо пустая строка."
    if new_weapon["ammo"]:
        if not 0 <= int(new_weapon["ammo"]) <= 30:
            weapon_errors["ammo"] = "Значением может быть только число от 0 до 30"
    else:
        weapon_errors["ammo"] = "Значение не может быть пустым"

    if weapon_errors:
        return render_template("add_weapon.html", form=new_weapon, errors=weapon_errors)

    keys, placeholder = execute_param(new_weapon)

    cursor.execute(
        f"INSERT INTO weapons ({keys}) VALUES ({placeholder});",
        tuple(new_weapon.values()),
    )

    connection.commit()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
