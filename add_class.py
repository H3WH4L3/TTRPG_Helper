import re
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, g, session
from dotenv import load_dotenv
import os

load_dotenv()


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
connection = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
)
cursor = connection.cursor()

VALIDATION_TEXT = {
    "empty": "Значение не может быть пустым",
    "slug": "Только латиница, нижний регистр, слова через _",
    "name": "Только кирриллица, слова разделяются пробелом, никаких символов",
    "desc": "Только кориллица, допускается любой свободный форма, в конце точка",
    "formula": "Только формат вида XdY/XdY±Z (3d6/3d6±2)",
    "dublicate": "Такой id уже есть в базе!",
    "count": "Только число от 0 до {} (включительно)",
    "or_empty": ". Либо оставьте пустым.",
}


def validate_form(slug=None, name=None, describe=None, formula=None, count=None):
    if slug:
        return re.fullmatch(r"^[a-z]+(?:_[a-z]+)*$", slug)
    if name:
        return re.fullmatch(r"^[А-ЯЁ][а-яё]+(?: [А-ЯЁа-яё]+)*$", name)
    if describe:
        return re.fullmatch(r"^[А-ЯЁ][А-ЯЁа-яё0-9 ,:;()\-!?]*\.$", describe)
    if formula:
        return re.fullmatch(r"(?:(\d*)d)?(\d+)([+\-])?(\d+)?", formula)
    if count:
        return 0 <= int(count[0]) <= count[1]


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


def simple_upload_db(db_fragment, table):

    keys, placeholders = execute_param(db_fragment)
    cursor.execute(
        f"""
                    INSERT INTO {table}
                    (
                    {keys}
                    )
                    VALUES ({placeholders})
                    """,
        tuple(db_fragment.values()),
    )


def upload_db_returning(db_fragment, table, class_id):

    keys, placeholders = execute_param(db_fragment)

    # UPLOAD ELEMENT TO MAIN TABLE
    cursor.execute(
        f"INSERT INTO {table} ({keys}) VALUES ({placeholders}) RETURNING id;",
        tuple(db_fragment.values()),
    )
    element_id = cursor.fetchone()[0]

    # ADDING LINK BETWEEN ID
    cursor.execute(
        f"INSERT INTO {"class_" + table} (class_id, {table + "_id"}) VALUES ({class_id}, {element_id});"
    )


def check_for_valid(form, table, slugs=None):
    errors = {}

    # UNIQUE SLUGS
    if not slugs:
        cursor.execute(f"SELECT slug FROM {table}")
        slugs = [i[0] for i in cursor.fetchall()]

    # SLUG
    if "slug" in form.keys():
        if not form["slug"]:
            errors["slug"] = VALIDATION_TEXT["empty"]
        elif not validate_form(slug=form["slug"]):
            errors["slug"] = VALIDATION_TEXT["slug"]
        elif form["slug"] in slugs:
            errors["slug"] = VALIDATION_TEXT["dublicate"]

    # NAME
    if "name_ru" in form.keys():
        if not form["name_ru"]:
            errors["name_ru"] = VALIDATION_TEXT["empty"]
        elif not validate_form(name=form["name_ru"]):
            errors["name_ru"] = VALIDATION_TEXT["name"]

    # DESCRIBE
    if "desc_ru" in form.keys():
        if not form["desc_ru"]:
            errors["desc_ru"] = VALIDATION_TEXT["empty"]
        elif not validate_form(describe=form["desc_ru"]):
            errors["desc_ru"] = VALIDATION_TEXT["desc"]

    # TEXT
    if "text_ru" in form.keys():
        if not form["text_ru"]:
            errors["text_ru"] = VALIDATION_TEXT["empty"]
        elif not validate_form(describe=form["text_ru"]):
            errors["test_ru"] = VALIDATION_TEXT["desc"]

    # ARMOR LEVE
    if "armor_level" in form.keys():
        if not form["armor_level"]:
            errors["armor_level"] = VALIDATION_TEXT["empty"]
        elif not validate_form(count=(form["armor_level"], 10)):
            errors["armor_level"] = VALIDATION_TEXT["count"].format(10)

    # EFFECT
    if "effect" in form.keys() and form["effect"]:
        if not validate_form(describe=form["effect"]):
            errors["effect"] = VALIDATION_TEXT["desc"] + VALIDATION_TEXT["or_empty"]

    # DAMAGE
    if "damage" in form.keys():
        if not form["damage"]:
            errors["damage"] = VALIDATION_TEXT["empty"]
        elif not validate_form(formula=form["damage"]):
            errors["damage"] = VALIDATION_TEXT["formula"]

    # AMMO
    if "ammo" in form.keys() and form["ammo"]:
        if not validate_form(count=(form["ammo"], 60)):
            errors["ammo"] = (
                VALIDATION_TEXT["count"].format(60) + VALIDATION_TEXT["or_empty"]
            )

    # COUNTS
    if "counts" in form.keys() and form["counts"]:
        if not validate_form(describe=form["counts"]):
            errors["counts"] = VALIDATION_TEXT["desc"] + VALIDATION_TEXT["or_empty"]

    # COST
    if "cost" in form.keys() and form["cost"]:
        if not validate_form(describe=form["cost"]):
            errors["cost"] = VALIDATION_TEXT["desc"] + VALIDATION_TEXT["or_empty"]

    # FORMULA
    if form:
        for key, value in form.items():
            if key.endswith("formula"):
                if not validate_form(formula=value):
                    errors[key] = VALIDATION_TEXT["formula"]

    return errors


# MAIN PAGE
@app.route("/")
def index():
    return render_template("index.html")


# ADD NEW CLASS
@app.route("/add_class", methods=["POST", "GET"])
def add_class():
    if request.method == "GET":
        return render_template("add_class.html", form={}, errors={})

    columns = (
        "slug",
        "name_ru",
        "desc_ru",
        "hp_formula",
        "signs_formula",
        "agility_formula",
        "presence_formula",
        "strength_formula",
        "toughness_formula",
        "weapon_formula",
        "armor_forumla",
    )
    new_class = {}
    for column in columns:
        new_class[column] = request.form.get(column, "").strip()

    # VALIDATION
    errors = check_for_valid(new_class)
    if errors:
        return render_template("add_class.html", errors=errors, form=new_class)

    # UPLOAD TO DB
    db_class = new_class.copy()
    simple_upload_db(db_class, "classes")

    connection.commit()
    return redirect(url_for("index"))


# ADD NEW SKILL
@app.route("/add_skill", methods=["POST", "GET"])
def add_skill():
    # CLASSES
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

    # VALIDATION
    for i in range(len(slugs)):
        form = {
            "slug": slugs[i].strip(),
            "name_ru": names[i].strip(),
            "desc_ru": descs[i].strip(),
        }
        error = check_for_valid(form, " skills")
        errors.append(error)
        new_skill.append(form)

    if any(errors):
        return render_template(
            "add_skill.html",
            form=new_skill,
            errors=errors,
            classes=classes,
            selected_class_id=class_id,
        )

    # UPLOAD TO DB
    db_skill = new_skill.copy()
    for skill in db_skill:
        upload_db_returning(skill, "skills", class_id)

    connection.commit()
    return redirect(url_for("index"))


# ADD NEW BONUS
@app.route("/add_bonus", methods=["POST", "GET"])
def add_bonus():
    # CLASSES
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

    # VALIDATION
    new_bonus = []
    errors = []

    for i in range(len(slugs)):
        form = {
            "slug": slugs[i].strip(),
            "name_ru": names[i].strip(),
            "desc_ru": descs[i].strip(),
        }
        error = check_for_valid(form, "bonuses")

        errors.append(error)
        new_bonus.append(form)

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

    # UPLOAD TO DB
    db_bonuses = new_bonus.copy()
    cursor.execute(
        "UPDATE classes SET bonus_type=%s WHERE id=%s",
        (bonus_type, int(class_id)),
    )
    for bonus in db_bonuses:
        upload_db_returning(bonus, "bonuses", class_id)

    connection.commit()
    return redirect(url_for("index"))


# ADD NEW MEMORIE
@app.route("/add_memorie", methods=["POST", "GET"])
def add_memorie():
    # CLASSES
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

    # VALIDATION
    new_memorie = []
    errors = []

    for i in range(len(slugs)):
        memorie_error = {}
        form = {
            "slug": slugs[i].strip(),
            "name_ru": names[i].strip(),
            "desc_ru": descs[i].strip(),
        }
        error = check_for_valid(form, "memories")
        errors.append(error)
        new_memorie.append(form)

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

    # UPLOAD TO DB
    db_memorie = new_memorie.copy()
    cursor.execute(
        "UPDATE classes SET memorie_type=%s WHERE id=%s",
        (memorie_type, int(class_id)),
    )

    for memorie in db_memorie:
        upload_db_returning(memorie, "memories", class_id)
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
    new_narrative["slug"] = request.form.get("slug", "").strip()
    new_narrative["category"] = request.form.get("category", "").strip()
    new_narrative["text_ru"] = request.form.get("text_ru", "").strip()

    # VALIDATION
    cursor.execute(
        "SELECT slug FROM narrative WHERE category=%s", (new_narrative["category"],)
    )
    slugs_narrative = [i[0] for i in cursor.fetchall()]
    errors = check_for_valid(new_narrative, "narrative", slugs_narrative)

    if errors:
        return render_template(
            "add_narrative.html",
            form=new_narrative,
            errors=errors,
            categories=categories,
            selected_category=new_narrative["category"],
        )

    # UPLOAD TO DB
    db_narrative = new_narrative.copy()
    simple_upload_db(db_narrative, "narrative")

    connection.commit()
    return redirect(url_for("index"))


# ADD ARMOR
@app.route("/add_armor", methods=["POST", "GET"])
def add_armor():
    table = "armors"
    if request.method == "GET":
        return render_template("add_armor.html", form={}, errors={})

    # GETTING ALL VALUES
    new_armor = {}
    new_armor["slug"] = request.form.get("slug", "").strip()
    new_armor["name_ru"] = request.form.get("name_ru", "").strip()
    new_armor["armor_level"] = request.form.get("armor_level", "").strip()
    new_armor["effect"] = request.form.get("effect", "").strip()

    # VALIDATION
    errors = check_for_valid(new_armor, table)
    if errors:
        return render_template("add_armor.html", form=new_armor, errors=errors)

    # UPLOAD TO BASE
    db_armor = new_armor.copy()
    db_armor["armor_level"] = (
        int(db_armor["armor_level"]) if db_armor["armor_level"] else None
    )
    db_armor["effect"] = db_armor["effect"] if db_armor["effect"] else None
    simple_upload_db(db_armor, table)
    connection.commit()

    return redirect(url_for("index"))


# ADD WEAPON
@app.route("/add_weapon", methods=["POST", "GET"])
def add_weapon():
    table = "weapons"
    if request.method == "GET":
        return render_template("add_weapon.html", form={}, errors={})

    new_weapon = {}
    new_weapon["slug"] = request.form.get("slug", "").strip()
    new_weapon["name_ru"] = request.form.get("name_ru", "").strip()
    new_weapon["damage"] = request.form.get("damage", "").strip()
    new_weapon["effect"] = request.form.get("effect", "").strip()
    new_weapon["ammo"] = request.form.get("ammo", "").strip()

    errors = check_for_valid(new_weapon, table)
    if errors:
        return render_template("add_weapon.html", form=new_weapon, errors=errors)

    db_weapon = new_weapon.copy()
    db_weapon["effect"] = db_weapon["effect"] if db_weapon["effect"] else None
    db_weapon["ammo"] = int(db_weapon["ammo"]) if db_weapon["ammo"] else None

    simple_upload_db(db_weapon, table)
    connection.commit()

    return redirect(url_for("index"))


# ADD ITEMS
@app.route("/add_item", methods=["POST", "GET"])
def add_item():
    categories = [
        ("", "Ничего"),
        ("sacred_scroll", "Священный свиток"),
        ("wicked_scroll", "Проклятый свиток"),
    ]
    if request.method == "GET":
        return render_template(
            "add_item.html", form={}, error={}, categories=categories
        )

    new_item = {}
    new_item["slug"] = request.form.get("slug", "").strip()
    new_item["name_ru"] = request.form.get("name_ru", "").strip()
    new_item["effect"] = request.form.get("effect", "").strip()
    new_item["counts"] = request.form.get("counts", "").strip()
    new_item["cost"] = request.form.get("cost", "").strip()
    new_item["category"] = request.form.get("category", "").strip()

    # VALIDATION
    errors = check_for_valid(new_item, "items")

    if errors:
        return render_template(
            "add_item.html", form=new_item, error=errors, categories=categories
        )

    # UPLOAD TO DB
    db_item = new_item.copy()
    db_item["effect"] = db_item["effect"] if db_item["effect"] else None
    db_item["counts"] = db_item["counts"] if db_item["counts"] else None
    db_item["cost"] = int(db_item["cost"]) if db_item["cost"] else None

    simple_upload_db(db_item, "items")

    connection.commit()
    return redirect(url_for("index"))


# PATH # 1
@app.route("/path/class", methods=["POST", "GET"])
def path_class():
    if "final_step" not in session:
        session["final_step"] = False
    if request.method == "GET":
        return render_template("add_class.html", form={}, errors={})

    columns = (
        "slug",
        "name_ru",
        "desc_ru",
        "hp_formula",
        "money_formula",
        "signs_formula",
        "agility_formula",
        "presence_formula",
        "strength_formula",
        "toughness_formula",
        "weapon_formula",
        "armor_formula",
    )

    new_class = {}
    for column in columns:
        new_class[column] = request.form.get(column, "").strip()

    errors = check_for_valid(new_class, "classes")

    if errors:
        return render_template("add_class.html", form=new_class, errors=errors)

    session["class"] = new_class
    if session["final_step"]:
        return redirect(url_for("confirm_result"))

    return redirect(url_for("path_skills"))


# PATH # 2
@app.route("/path/skills", methods=["POST", "GET"])
def path_skills():
    if request.method == "GET":
        empty_skill = {"slug": "", "name_ru": "", "desc_ru": ""}
        return render_template(
            "add_skill.html",
            form=[empty_skill],
            errors=[{}],
            choosen_class=session["class"]["name_ru"],
        )

    slugs = request.form.getlist("slug[]")
    names = request.form.getlist("name_ru[]")
    descs = request.form.getlist("desc_ru[]")

    new_skill = []
    errors = []

    # VALIDATION
    for i in range(len(slugs)):
        form = {
            "slug": slugs[i].strip(),
            "name_ru": names[i].strip(),
            "desc_ru": descs[i].strip(),
        }
        error = check_for_valid(form, "skills")
        errors.append(error)
        new_skill.append(form)

    if any(errors):
        return render_template(
            "add_skill.html",
            form=new_skill,
            errors=errors,
            choosen_class=session["class"]["name_ru"],
        )
    session["skills"] = new_skill

    if session["final_step"]:
        return redirect(url_for("confirm_result"))

    return redirect(url_for("path_bonuses"))


# PATH # 3
@app.route("/path/bonuses", methods=["POST", "GET"])
def path_bonuses():
    if request.method == "GET":
        empty_bonus = {"slug": "", "name_ru": "", "desc_ru": ""}
        return render_template(
            "add_bonus.html",
            form=[empty_bonus],
            errors=[{}],
            bonus_type="",
            type_error="",
            choosen_class=session["class"]["name_ru"],
        )

    bonus_type = request.form.get("bonus_type", "").strip()

    if not validate_form(describe=bonus_type):
        type_error = VALIDATION_TEXT["desc"]
    else:
        type_error = ""

    slugs = request.form.getlist("slug[]")
    names = request.form.getlist("name_ru[]")
    descs = request.form.getlist("desc_ru[]")

    # VALIDATION
    new_bonus = []
    errors = []

    for i in range(len(slugs)):
        form = {
            "slug": slugs[i].strip(),
            "name_ru": names[i].strip(),
            "desc_ru": descs[i].strip(),
        }
        error = check_for_valid(form, "bonuses")

        errors.append(error)
        new_bonus.append(form)

    if any(errors) or type_error:
        return render_template(
            "add_bonus.html",
            form=new_bonus,
            errors=errors,
            bonus_type=bonus_type,
            type_error=type_error,
            choosen_class=session["class"]["name_ru"],
        )

    session["bonuses"] = new_bonus
    session["bonus_type"] = bonus_type

    if session["final_step"]:
        return redirect(url_for("confirm_result"))

    return redirect(url_for("path_memories"))


# PATH # 4
@app.route("/path/memories", methods=["POST", "GET"])
def path_memories():
    if request.method == "GET":
        empty_memorie = {"slug": "", "name_ru": "", "desc_ru": ""}
        return render_template(
            "add_memorie.html",
            form=[empty_memorie],
            errors=[{}],
            memorie_type="",
            type_error="",
            choosen_class=session["class"]["name_ru"],
        )

    memorie_type = request.form.get("memorie_type", "").strip()

    if not validate_form(describe=memorie_type):
        type_error = VALIDATION_TEXT["desc"]
    else:
        type_error = ""

    slugs = request.form.getlist("slug[]")
    names = request.form.getlist("name_ru[]")
    descs = request.form.getlist("desc_ru[]")

    # VALIDATION
    new_memorie = []
    errors = []

    for i in range(len(slugs)):
        form = {
            "slug": slugs[i].strip(),
            "name_ru": names[i].strip(),
            "desc_ru": descs[i].strip(),
        }
        error = check_for_valid(form, "memories")
        errors.append(error)
        new_memorie.append(form)

    if any(errors) or type_error:
        return render_template(
            "add_memorie.html",
            form=new_memorie,
            errors=errors,
            memorie_type=memorie_type,
            type_error=type_error,
            choosen_class=session["class"]["name_ru"],
        )

    session["memories"] = new_memorie
    session["memorie_type"] = memorie_type

    return redirect(url_for("confirm_result"))


# Confirm Full Class valuation before uploading
@app.route("/path/confirm", methods=["POST", "GET"])
def confirm_result():
    if request.method == "GET":
        session["final_step"] = True
        return render_template("confirm_result.html", session=session)

    # IF WE WANT TO CHANGE SOMETHING
    action = request.form.get("action")
    if action == "change_class":
        return render_template("add_class.html", form=session["class"], errors={})
    elif action == "change_skills":
        return render_template(
            "add_skills.html",
            form=session["skills"],
            choosen_class=session["class"]["name_ru"],
            errors=[{}],
        )
    elif action == "change_bonuses":
        return render_template(
            "add_bonuses.html",
            form=session["bonuses"],
            bonus_type=session["bonus_type"],
            choosen_class=session["class"]["name_ru"],
            errors=[{}],
            type_error="",
        )
    elif action == "change_memories":
        return render_template(
            "add_memories.html",
            form=session["memories"],
            memorie_type=session["memorie_type"],
            choosen_class=session["class"]["name_ru"],
            errors=[{}],
            type_error="",
        )

    # UPLOAD TO DB

    # CLASS
    keys, placeholders = execute_param(session["class"])
    cursor.execute(
        f"INSERT INTO classes ({keys}) VALUES ({placeholders}) RETURNING id;",
        tuple(session["class"].values()),
    )
    class_id = cursor.fetchone()[0]

    # SKILLS
    for skill in session["skills"]:
        upload_db_returning(skill, "skills", class_id)

        # BONUSES
    cursor.execute(
        "UPDATE classes SET bonus_type = %s WHERE id = %s",
        (session["bonus_type"], class_id),
    )

    for bonus in session["bonuses"]:
        upload_db_returning(bonus, "bonuses", class_id)

        # MEMORIES
    cursor.execute(
        "UPDATE classes SET memorie_type = %s WHERE id = %s",
        (session["memorie_type"], class_id),
    )
    for memorie in session["memories"]:
        upload_db_returning(memorie, "memories", class_id)
    connection.commit()

    session.clear()
    return redirect(url_for("index"))


# Delete Tests Valuation from DB
@app.route("/path/delete_test", methods=["POST"])
def delete_test():
    with connection:
        # Chained data first
        cursor.execute(
            "DELETE FROM class_bonuses "
            "WHERE class_id IN (SELECT id FROM classes WHERE slug LIKE 'test_%');"
        )
        cursor.execute(
            "DELETE FROM class_memories "
            "WHERE class_id IN (SELECT id FROM classes WHERE slug LIKE 'test_%');"
        )
        cursor.execute(
            "DELETE FROM class_skills "
            "WHERE class_id IN (SELECT id FROM classes WHERE slug LIKE 'test_%');"
        )

        # Main tables second
        cursor.execute("DELETE FROM bonuses  WHERE slug LIKE 'test_%';")
        cursor.execute("DELETE FROM memories WHERE slug LIKE 'test_%';")
        cursor.execute("DELETE FROM skills   WHERE slug LIKE 'test_%';")

        # Class table third
        cursor.execute("DELETE FROM classes  WHERE slug LIKE 'test_%';")

    return "ok", 200


if __name__ == "__main__":
    app.run(debug=True)
