# views/main_view.py
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QTabWidget, QMessageBox, QToolBar
)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import QTimer, QSize
import sqlite3
from pathlib import Path
from PyQt6.QtCore import Qt
from .clientes_view import ClientesWindow
from .servicios_view import ServiciosWindow
from .ventas_view import VentasWindow
from .reportes_view import ReportesWindow


def _icon(name: str) -> QIcon:
    """Carga un icono de assets/icons/<name>. Si no existe, devuelve un QIcon vacío."""
    icon_path = Path(__file__).resolve().parent.parent / "assets" / "icons" / name
    return QIcon(str(icon_path)) if icon_path.exists() else QIcon()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clínica Dental POS")
        self.setGeometry(200, 200, 900, 600)

        # Ícono de ventana
        tooth = _icon("icon.png")
        if not tooth.isNull():
            self.setWindowIcon(tooth)

        # ----- Toolbar con iconos -----
        toolbar = QToolBar("Acciones")
        toolbar.setIconSize(QSize(28, 28))
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.addToolBar(toolbar)

        self.action_clientes = QAction(_icon("users.png"), "Clientes", self)
        self.action_clientes.setToolTip("Administrar Clientes")
        self.action_clientes.triggered.connect(self.abrir_clientes)
        toolbar.addAction(self.action_clientes)


        self.action_servicios = QAction(_icon("tools.png"), "Servicios", self)
        self.action_servicios.setToolTip("Administrar Servicios")
        self.action_servicios.triggered.connect(self.abrir_servicios)
        toolbar.addAction(self.action_servicios)

        self.action_ventas = QAction(_icon("cart.png"), "Ventas", self)
        self.action_ventas.setToolTip("Registrar Nueva Venta")
        self.action_ventas.triggered.connect(self.abrir_ventas)
        toolbar.addAction(self.action_ventas)

        toolbar.addSeparator()

        self.action_actualizar = QAction(_icon("refresh.png"), "Actualizar", self)
        self.action_actualizar.setToolTip("Actualizar resúmenes (F5)")
        self.action_actualizar.setShortcut("F5")
        self.action_actualizar.triggered.connect(self.cargar_resumenes)
        toolbar.addAction(self.action_actualizar)

        toolbar.addSeparator()

        self.action_reportes = QAction(_icon("report.png"), "Reportes", self)
        self.action_reportes.setToolTip("Exportar Reportes a Excel")
        self.action_reportes.triggered.connect(self.abrir_reportes)
        toolbar.addAction(self.action_reportes)

        # ----- Contenedor central -----
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ----- Tabs con resúmenes -----
        self.tabs = QTabWidget()

        # Tabla clientes
        self.tab_clientes = QTableWidget()
        self._prep_table(self.tab_clientes)
        self.tabs.addTab(self.tab_clientes, "Clientes")

        # Tabla servicios (solo nombre)
        self.tab_servicios = QTableWidget()
        self._prep_table(self.tab_servicios)
        self.tabs.addTab(self.tab_servicios, "Servicios")

        # Tabla ventas (usa servicios_texto)
        self.tab_ventas = QTableWidget()
        self._prep_table(self.tab_ventas)
        self.tabs.addTab(self.tab_ventas, "Ventas")

        layout.addWidget(self.tabs)
        central_widget.setLayout(layout)

        # Cargar datos iniciales
        self.cargar_resumenes()

        # --- Timer de actualización automática (60s)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.cargar_resumenes)
        self.timer.start(60000)

        # Barra de estado
        self.statusBar().showMessage("Resumenes")

    # ----- Utilidad tabla -----
    def _prep_table(self, table: QTableWidget):
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.setSortingEnabled(True)

    # ----- Carga de resúmenes -----
    def cargar_resumenes(self):
        try:
            conn = sqlite3.connect("clinica.db")
            cursor = conn.cursor()

            # Resumen de clientes
            cursor.execute("SELECT nombre, telefono FROM clientes ORDER BY id DESC LIMIT 50")
            rows = cursor.fetchall()
            self._llenar_tabla(self.tab_clientes, rows, [ "Nombre", "Teléfono"])

            # Resumen de servicios
            cursor.execute("SELECT nombre FROM servicios ORDER BY id DESC LIMIT 50")
            rows = cursor.fetchall()
            self._llenar_tabla(self.tab_servicios, rows, [ "Servicio"])

            # Resumen de ventas
            cursor.execute("""
                SELECT  c.nombre AS cliente, v.servicios_texto AS servicios, v.monto, v.fecha
                FROM ventas v
                LEFT JOIN clientes c ON v.cliente_id = c.id
                ORDER BY v.id DESC
                LIMIT 50
            """)
            rows = cursor.fetchall()
            self._llenar_tabla(self.tab_ventas, rows, ["Cliente", "Servicios", "Monto", "Fecha"])

            conn.close()

            # Ajuste de columnas al contenido
            for t in (self.tab_clientes, self.tab_servicios, self.tab_ventas):
                t.resizeColumnsToContents()

            self.statusBar().showMessage("Resúmenes actualizados")
        except Exception as e:
            QMessageBox.warning(self, "Error de BD", f"No se pudieron cargar los resúmenes:\n{e}")

    def _llenar_tabla(self, tabla: QTableWidget, datos, headers):
        tabla.setSortingEnabled(False)
        tabla.clear()
        tabla.setRowCount(len(datos))
        tabla.setColumnCount(len(headers))
        tabla.setHorizontalHeaderLabels(headers)
        for i, row in enumerate(datos):
            for j, value in enumerate(row):
                tabla.setItem(i, j, QTableWidgetItem(str(value)))
        tabla.setSortingEnabled(True)

    # ----- Ventanas secundarias -----
    def abrir_clientes(self):
        self.clientes_view = ClientesWindow()
        self.clientes_view.show()

    def abrir_servicios(self):
        self.servicios_view = ServiciosWindow()
        self.servicios_view.show()

    def abrir_ventas(self):
        self.ventas_view = VentasWindow()
        self.ventas_view.show()

    def abrir_reportes(self):
        self.reportes_view = ReportesWindow()
        self.reportes_view.show()
