# main.py
import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from views.main_view import MainWindow
import database  # 👈 importante para init_db()
database.init_db()

APP_FOLDER_NAME = "ClinicaDentalPOS"

def ensure_user_folders():
    """
    Crea en Documentos:
      - ClinicaDentalPOS\Tickets
      - ClinicaDentalPOS\Reportes
    y expone rutas por variables de entorno (útil si luego las lees en las views).
    """
    docs_dir = Path.home() / "Documents"
    base_dir = docs_dir / APP_FOLDER_NAME
    tickets_dir = base_dir / "Tickets"
    reportes_dir = base_dir / "Reportes"

    for d in (tickets_dir, reportes_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Variables de entorno por si las quieres leer en tus views
    os.environ["CLINICA_POS_BASE_DIR"] = str(base_dir)
    os.environ["CLINICA_POS_TICKETS_DIR"] = str(tickets_dir)
    os.environ["CLINICA_POS_REPORTES_DIR"] = str(reportes_dir)

    print(f"[DIR] Base: {base_dir}")
    print(f"[DIR] Tickets: {tickets_dir}")
    print(f"[DIR] Reportes: {reportes_dir}")

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

    # Ícono
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

    # 1) Crea carpetas en Documentos
    ensure_user_folders()

    # 2) Inicializa / migra BD y hace seed de servicios
    database.init_db()

    # 3) UI
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
