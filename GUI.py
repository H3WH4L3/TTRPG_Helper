import sys
import db_data_funcs as db
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from main_generate import MBCharacter

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QTextEdit,
    QHBoxLayout,
    QVBoxLayout,
    QDialog,
    QListWidget,
    QMainWindow,
    QLabel,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, QTimer, QSize, Qt
from PyQt6.QtGui import QPixmap


# --- GENERATION WEB ---
class WebWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._REPO_ROOT = Path(__file__).resolve().parent
        self._TEMPLATES_DIR = self._REPO_ROOT / "templates"
        self._STATIC_DIR = self._REPO_ROOT / "static"
        self._EXPORT_DIR = self._REPO_ROOT / "exports"
        self._EXPORT_DIR.mkdir(exist_ok=True)
        self._PAGES = [
            "character_local_one.html",
            "character_local_two.html",
            "character_local_three.html",
            "character_local_four.html",
            "character_local_five.html",
        ]

        self.view = QWebEngineView()
        self.setCentralWidget(self.view)

        self.env = Environment(
            loader=FileSystemLoader(self._TEMPLATES_DIR), autoescape=True
        )

        self._page_index = 0
        self._character = self.generate_character()

        self.view.loadFinished.connect(self._on_loaded)

        self.resize(1200, 800)
        self.setWindowFlag(Qt.WindowType.Tool, True)
        self.showMinimized()

        QTimer.singleShot(0, self._load_current_page)

    def on_loaded(self):
        QTimer.singleShot(300, self.save_to_image)

    def _grab_and_restore(self, original_size, filename="character.png"):
        pixmap = self.view.grab()
        pixmap.save(filename)

        self.view.resize(original_size)

    def save_to_image(self, filename="character.png"):
        page = self.view.page()

        size = page.contentsSize()
        full_size = QSize(int(size.width()), int(size.height()))
        original_size = self.view.size()
        self.view.resize(full_size)

        QTimer.singleShot(200, lambda: self._grab_and_restore(original_size))

    def generate_character(self):
        test = MBCharacter()
        test.generate()
        return dict(test.character.__dict__)

    def _load_current_page(self):
        if self._page_index >= len(self._PAGES):
            self.close()
            return

        tpl_name = self._PAGES[self._page_index]
        template = self.env.get_template(tpl_name)
        html = template.render(character=self._character)

        self.view.setHtml(
            html, baseUrl=QUrl.fromLocalFile(str(self._REPO_ROOT.resolve()) + "/")
        )

    def _on_loaded(self, ok):
        if not ok:
            print("Не загрузилось")
            self._page_index += 1
            self._load_current_page()
            return

        QTimer.singleShot(300, self._save_current_page)

    def _save_current_page(self):
        page = self.view.page()
        sizef = page.contentsSize()

        full_size = QSize(int(sizef.width()), int(sizef.height()))
        original_size = self.view.size()

        self.view.resize(full_size)

        QTimer.singleShot(200, lambda: self._grab_and_next(original_size))

    def _grab_and_next(self, original_size):
        filename = self._EXPORT_DIR / f"{self._page_index + 1:02d}.png"
        pixmap = self.view.grab()
        pixmap.save(str(filename))

        self.view.resize(original_size)

        self._page_index += 1
        self._load_current_page()


# --- IMAGES  ---
class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Character Viewer")
        self.resize(1000, 800)

        self.label = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(self.label)

        self.images = sorted(Path("exports").glob("*.png"))
        self.index = 0

        self.show_image()

    def show_image(self):
        pixmap = QPixmap(str(self.images[self.index]))
        self.label.setPixmap(
            pixmap.scaled(
                self.label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Right:
            self.index = (self.index + 1) % len(self.images)
            self.show_image()

        elif event.key() == Qt.Key.Key_Left:
            self.index = (self.index - 1) % len(self.images)
            self.show_image()


# --- CHOOSE CLASS ---
class ClassSelectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Выбор класса")

        self.lst = QListWidget()
        for row in db.show_all_classes():
            self.lst.addItem(row["name_ru"])

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(self.lst)
        layout.addWidget(ok_btn)

    def selected_class(self):
        item = self.lst.currentItem()
        return item.text() if item else None


# --- CHOOSE NARATIVE CATEGORY ---
class NarativeSelectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Выбор наратива")

        self.lst = QListWidget()
        for row in db.show_all_classes():
            self.lst.addItem(row["name_ru"])

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(self.lst)
        layout.addWidget(ok_btn)

    def selected_class(self):
        item = self.lst.currentItem()
        return item.text() if item else None


# --- MAIN CLASS ---
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.narative_list = {
            "Вредная привычка": "bad_habit",
            "Опасное прошлое": "dangerous_past",
            "Ужасная черта": "terrible_trait",
            "Травма": "injurie",
            "Секретный твист": "secret_quest",
        }
        # region --- MAIN POSITION ---
        root = QHBoxLayout(self)
        # endregion

        # region --- LEFT SIDE-BAR ---
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        left_layout.addStretch()
        root.addWidget(left_widget)

        # endregion

        # region --- INFO BUTTONS ---
        # CLASSES BUTTON
        self.btn_cls = QPushButton("Показать классы")
        self.btn_cls.clicked.connect(
            lambda: self.show_all_names("classes", db.show_all_classes)
        )
        # SKILLS
        self.btn_skl = QPushButton("Показать скиллы")
        self.btn_skl.clicked.connect(
            lambda: self.show_all_names("skills", db.show_all_skills)
        )
        # ARMORS
        self.btn_armr = QPushButton("Показать броню")
        self.btn_armr.clicked.connect(
            lambda: self.show_all_names("armors", db.show_all_armors)
        )
        # WEAPONS
        self.btn_wpn = QPushButton("Показать оружие")
        self.btn_wpn.clicked.connect(
            lambda: self.show_all_names("weaapons", db.show_all_weapons)
        )
        # ITEMS
        self.btn_itm = QPushButton("Показать предметы")
        self.btn_itm.clicked.connect(
            lambda: self.show_all_names("items", db.show_all_items)
        )
        # BONUSES
        self.btn_bonus = QPushButton("Показать бонусы")
        self.btn_bonus.clicked.connect(self.show_bonuses)
        # MEMORIES
        self.btn_memorie = QPushButton("Показать воспоминания")
        self.btn_memorie.clicked.connect(self.show_memories)
        # NARRATIVE
        self.btn_narative = QPushButton("Показать нарратив")
        self.btn_narative.clicked.connect(self.show_narative)
        # GENERATE
        self.btn_generate = QPushButton("Сгенерировать персонажа")
        self.btn_generate.clicked.connect(self.open_web)
        # IMAGES
        self.btn_img = QPushButton("Открыть просмотрщик")
        self.btn_img.clicked.connect(self.open_viewer)

        left_layout.addWidget(self.btn_cls)
        left_layout.addWidget(self.btn_armr)
        left_layout.addWidget(self.btn_itm)
        left_layout.addWidget(self.btn_skl)
        left_layout.addWidget(self.btn_wpn)
        left_layout.addWidget(self.btn_bonus)
        left_layout.addWidget(self.btn_memorie)
        left_layout.addWidget(self.btn_narative)
        left_layout.addWidget(self.btn_generate)
        left_layout.addWidget(self.btn_img)
        # endregion

        # region --- CONTENT WINDOW ---
        self.output = QListWidget()
        self.output.itemClicked.connect(self.on_item_clicked)
        self.current_mode = None

        root.addWidget(self.output, 1)

        self.main_output = QTextEdit()
        self.main_output.setReadOnly(True)
        root.addWidget(self.main_output, 2)
        # endregion

    # --- Standart Buttons ---
    def show_all_names(self, mode, func):
        self.output.clear()
        self.main_output.clear()
        self.current_mode = mode

        rows = func()
        text = [r["name_ru"] for r in rows]
        for el in text:
            self.output.addItem(el)

    def on_item_clicked(self, item):
        name = item.text()

        handlers = {
            "classes": self.show_class_details,
            "items": self.show_item_details,
            "weapons": self.show_weapon_details,
            "armors": self.show_armor_details,
            "skills": self.show_skill_details,
            "bonuses": self.show_bonus_details,
            "memories": self.show_memorie_details,
            "narative": self.show_narative_details,
        }

        handler = handlers.get(self.current_mode)
        if not handler:
            self.main_output.setPlainText("Не выбран режим списка.")
            return

        handler(name)

    # region --- SHOW INFO LOGIC ---
    def show_class_details(self, name):
        info = db.show_info_classes(name)
        text = "\n".join([f"{k}: {v}" for k, v in info.items()])
        self.main_output.setPlainText(text)

    def show_item_details(self, name):
        info = db.show_info_items(name)
        text = "\n".join([f"{k}: {v}" for k, v in info.items()])
        self.main_output.setPlainText(text)

    def show_weapon_details(self, name):
        info = db.show_info_weapons(name)
        text = "\n".join([f"{k}: {v}" for k, v in info.items()])
        self.main_output.setPlainText(text)

    def show_armor_details(self, name):
        info = db.show_info_armor(name)
        text = "\n".join([f"{k}: {v}" for k, v in info.items()])
        self.main_output.setPlainText(text)

    def show_skill_details(self, name):
        info = db.show_info_skill(name)
        text = "\n".join([f"{k}: {v}" for k, v in info.items()])
        self.main_output.setPlainText(text)

    def show_bonus_details(self, name):
        info = db.show_info_bonuses(name)
        text = "\n".join([f"{k}: {v}" for k, v in info.items()])
        self.main_output.setPlainText(text)

    def show_memorie_details(self, name):
        info = db.show_info_memories(name)
        text = "\n".join([f"{k}: {v}" for k, v in info.items()])
        self.main_output.setPlainText(text)

    def show_narative_details(self, name):
        name = self.narative_list[name]
        info = db.show_all_narratives(name)
        text = "\n\n".join(info)
        self.main_output.setPlainText(text)

    # endregion

    def show_bonuses(self):
        self.output.clear()
        self.current_mode = "bonuses"
        dialog = ClassSelectDialog(self)

        if dialog.exec():
            cls_name = dialog.selected_class()
            if not cls_name:
                return

            bonuses = db.show_all_bonuses(cls_name)

            for el in bonuses:
                self.output.addItem(el)

    def show_narative(self):
        self.output.clear()
        self.current_mode = "narative"

        for key in self.narative_list.keys():
            self.output.addItem(key)

    def show_memories(self):
        self.output.clear()
        self.current_mode = "memorie"
        dialog = ClassSelectDialog(self)

        if dialog.exec():
            cls_name = dialog.selected_class()
            if not cls_name:
                return

            memories = db.show_all_memories(cls_name)

            for el in memories:
                self.output.addItem(el)

    def open_web(self):
        self.web_window = WebWindow()
        self.web_window.show()

    def open_viewer(self):
        self.viewer = ImageViewer()
        self.viewer.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(800, 400)
    w.show()
    sys.exit(app.exec())
