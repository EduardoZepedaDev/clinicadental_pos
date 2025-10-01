# utils/paths.py
import sys
from pathlib import Path
import os

APP_NAME = "ClinicaDentalPOS"

def is_frozen() -> bool:
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")

def base_path() -> Path:
    # Carpeta donde están los recursos (themes, assets, templates) en dev o congelado
    if is_frozen():
        return Path(sys._MEIPASS)  # pyinstaller runtime dir
    return Path(__file__).resolve().parents[1]  # raíz del repo

def user_data_dir() -> Path:
    # %APPDATA%\ClinicaDentalPOS  (ej. C:\Users\<user>\AppData\Roaming\ClinicaDentalPOS)
    p = Path(os.getenv("APPDATA", Path.home())) / APP_NAME
    p.mkdir(parents=True, exist_ok=True)
    return p

def tickets_dir() -> Path:
    p = user_data_dir() / "tickets"
    p.mkdir(parents=True, exist_ok=True)
    return p

def db_path() -> Path:
    # BD en user_data para que el usuario no necesite permisos admin
    return user_data_dir() / "clinica.db"

def asset(*parts) -> Path:
    # Para cargar archivos de /assets, /themes, /templates, etc.
    return base_path().joinpath(*parts)
