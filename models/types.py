from typing import TypedDict


class Skills(TypedDict):
    """
    key     : Название, строка;
    value   : Текст, строка;
    """

    key: str


class Armor(TypedDict):
    """
    name  : Вид, строка;
    level : Уровень, число от 1 до 4;
    effect: Эффект, строка. Не обязательно;
    """

    name: str
    level: int
    effect: str | None


class Weapon(TypedDict):
    """
    name    : Вид, строка;
    damage  : Строка вида d4, число;
    effect  : Эффект, строка. Не обязательно;
    ammo    : Количество, число. Не обязательно;
    """

    name: str
    damage: str
    effect: str | None
    ammo: int | None


class Items(TypedDict):
    """
    key     : Название предмета. Внутри лежит dict
    -------
    effect  : Эффект, строка. Не обязательно;
    counts  : Количество, строка. Не обязательно;
    cost    : Цена, число. Не обязательно;
    """

    key: dict
    effect: str | None
    counts: str | None
    cost: int | None
