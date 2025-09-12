import sys
from PyQt6.QtWidgets import QApplication
from views.main_view import MainWindow
import database

if __name__ == "__main__":
    database.init_db()
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec())
