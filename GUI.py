import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
)

app = QApplication(sys.argv)
window = QMainWindow()
window.resize(500, 500)

with open("qstyles.qss") as f:
    app.setStyleSheet(f.read())

main = QWidget()
main_lt = QVBoxLayout()
main.setLayout(main_lt)
main_lt.setContentsMargins(0, 0, 0, 0)
main_lt.setSpacing(0)
window.setCentralWidget(main)

content_block = QWidget()
content_block.setObjectName("content_block_st")
content_block_lt = QHBoxLayout()
content_block.setLayout(content_block_lt)
content_block_lt.setContentsMargins(0, 0, 0, 0)
content_block_lt.setSpacing(0)

bottom_block = QWidget()
bottom_block.setObjectName("bottom_block_st")
bottom_block_lt = QHBoxLayout()
bottom_block.setLayout(bottom_block_lt)

main_lt.addWidget(content_block, 3)
main_lt.addWidget(bottom_block, 1)

bottom_button = QPushButton("Кнопка снизу")
bottom_block_lt.addWidget(bottom_button)

content_visualize_block = QWidget()
content_visualize_block_lt = QHBoxLayout()
content_visualize_block.setLayout(content_visualize_block_lt)

right_menu = QWidget()
right_menu.setObjectName("right_menu_st")
right_menu_lt = QVBoxLayout()
right_menu.setLayout(right_menu_lt)
right_menu_lt.setContentsMargins(0, 0, 0, 0)
right_menu_lt.setSpacing(0)

content_block_lt.addWidget(content_visualize_block, 3)
content_block_lt.addWidget(right_menu, 1)

right_button = QPushButton("Кнопка сбоку")
right_menu_lt.addWidget(right_button)
right_menu_lt.addStretch(1)

window.show()
app.exec()
