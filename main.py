# main.py
import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from views.main_view import MainWindow

def load_qss(app: QApplication, qss_path: Path):
    if qss_path.exists():
        css = qss_path.read_text(encoding="utf-8")
        app.setStyle("Fusion")
        app.setStyleSheet(css)
        print(f"[QSS] Tema aplicado: {qss_path}")
    else:
        print(f"[QSS] NO encontrado: {qss_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # === Ícono global de la aplicación ===
    icon_path = Path(__file__).resolve().parent / "assets" / "icons" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
        print(f"[ICON] Ícono aplicado: {icon_path}")
    else:
        print(f"[ICON] NO encontrado: {icon_path}")

    # Tema
    repo_root = Path(__file__).resolve().parent
    qss_file = repo_root / "themes" / "modern.qss"
    load_qss(app, qss_file)

    w = MainWindow()
    w.show()
    sys.exit(app.exec())
