from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMessageBox
import database
import pandas as pd
from pathlib import Path
import os

REPORTES_DIR = Path(os.getenv("CLINICA_POS_REPORTES_DIR",
                              Path.home() / "Documents" / "ClinicaDentalPOS" / "Reportes"))
REPORTES_DIR.mkdir(parents=True, exist_ok=True)
class ReportesWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reportes")
        self.setGeometry(350, 350, 300, 150)

        layout = QVBoxLayout()

        btn_exportar = QPushButton("Exportar Reporte a Excel", self)
        btn_exportar.clicked.connect(self.exportar_excel)
        layout.addWidget(btn_exportar)

        self.setLayout(layout)

    def exportar_excel(self):
        clientes = database.df_clientes()
        servicios = database.df_servicios()
        ventas = database.df_ventas()

        with pd.ExcelWriter("reporte_clinica.xlsx", engine="openpyxl") as writer:
            clientes.to_excel(writer, sheet_name="Clientes", index=False)
            servicios.to_excel(writer, sheet_name="Servicios", index=False)
            ventas.to_excel(writer, sheet_name="Ventas", index=False)

        QMessageBox.information(self, "Éxito", "Reporte exportado a reporte_clinica.xlsx")
