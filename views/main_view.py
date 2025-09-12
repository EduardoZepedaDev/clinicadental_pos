from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QTabWidget
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QTimer  # Importamos QTimer
import sqlite3

from .clientes_view import ClientesWindow
from .servicios_view import ServiciosWindow
from .ventas_view import VentasWindow
from .reportes_view import ReportesWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clínica POS")
        self.setGeometry(200, 200, 800, 600)

        # ----- Menú -----
        menubar = self.menuBar()

        menu_clientes = menubar.addMenu("Clientes")
        menu_servicios = menubar.addMenu("Servicios")
        menu_ventas = menubar.addMenu("Ventas")
        menu_reportes = menubar.addMenu("Reportes")

        action_clientes = QAction("Administrar Clientes", self)
        action_clientes.triggered.connect(self.abrir_clientes)
        menu_clientes.addAction(action_clientes)

        action_servicios = QAction("Administrar Servicios", self)
        action_servicios.triggered.connect(self.abrir_servicios)
        menu_servicios.addAction(action_servicios)

        action_ventas = QAction("Nueva Venta", self)
        action_ventas.triggered.connect(self.abrir_ventas)
        menu_ventas.addAction(action_ventas)

        action_reportes = QAction("Exportar a Excel", self)
        action_reportes.triggered.connect(self.abrir_reportes)
        menu_reportes.addAction(action_reportes)

        # ----- Contenedor central -----
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        # ----- Tabs con resúmenes -----
        self.tabs = QTabWidget()

        # Tabla clientes
        self.tab_clientes = QTableWidget()
        self.tabs.addTab(self.tab_clientes, "Clientes")

        # Tabla servicios
        self.tab_servicios = QTableWidget()
        self.tabs.addTab(self.tab_servicios, "Servicios")

        # Tabla ventas
        self.tab_ventas = QTableWidget()
        self.tabs.addTab(self.tab_ventas, "Ventas")

        layout.addWidget(self.tabs)
        central_widget.setLayout(layout)

        # Cargar datos iniciales desde SQLite
        self.cargar_resumenes()
        
        # --- NUEVO: Configuración del temporizador para actualizar cada minuto ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.cargar_resumenes)
        # El tiempo se establece en milisegundos: 1 minuto = 60,000 ms
        self.timer.start(60000)

    # ----- Métodos de conexión a SQLite -----
    def cargar_resumenes(self):
        conn = sqlite3.connect("clinica.db")
        cursor = conn.cursor()

        # Resumen de clientes
        cursor.execute("SELECT id, nombre, telefono FROM clientes LIMIT 10")
        rows = cursor.fetchall()
        self.llenar_tabla(self.tab_clientes, rows, ["ID", "Nombre", "Teléfono"])

        # Resumen de servicios
        cursor.execute("SELECT id, nombre, precio FROM servicios LIMIT 10")
        rows = cursor.fetchall()
        self.llenar_tabla(self.tab_servicios, rows, ["ID", "Servicio", "Precio"])

        # Resumen de ventas
        cursor.execute("""
            SELECT v.id, c.nombre AS cliente, s.nombre AS servicio, v.monto, v.fecha
            FROM ventas v
            JOIN clientes c ON v.cliente_id = c.id
            JOIN servicios s ON v.servicio_id = s.id
            ORDER BY v.id DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()
        self.llenar_tabla(self.tab_ventas, rows, ["ID", "Cliente", "Servicio", "Monto", "Fecha"])

        conn.close()

    def llenar_tabla(self, tabla, datos, headers):
        tabla.setRowCount(len(datos))
        tabla.setColumnCount(len(headers))
        tabla.setHorizontalHeaderLabels(headers)

        for i, row in enumerate(datos):
            for j, value in enumerate(row):
                tabla.setItem(i, j, QTableWidgetItem(str(value)))

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