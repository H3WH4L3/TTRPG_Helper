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


@app.route("/")
def index():
    return render_template("index.html")


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


if __name__ == "__main__":
    app.run(debug=True)
