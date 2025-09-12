from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QMessageBox, QTableWidget, QTableWidgetItem, QComboBox
)
import database


class VentasWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Ventas")
        self.setGeometry(400, 400, 600, 400)

        layout = QVBoxLayout()

        # --- Formulario ---
        self.cliente_id = QComboBox(self)
        self.cliente_id.setPlaceholderText("Selecciona Cliente")
        layout.addWidget(self.cliente_id)

        self.servicio_id = QComboBox(self)
        self.servicio_id.setPlaceholderText("Selecciona Servicio")
        layout.addWidget(self.servicio_id)

        self.monto = QLineEdit(self)
        self.monto.setPlaceholderText("Monto")
        layout.addWidget(self.monto)

        # --- Botones ---
        btn_layout = QHBoxLayout()

        self.btn_guardar = QPushButton("Registrar Venta", self)
        self.btn_guardar.clicked.connect(self.registrar_venta)
        btn_layout.addWidget(self.btn_guardar)

        self.btn_eliminar = QPushButton("Eliminar Venta", self)
        self.btn_eliminar.clicked.connect(self.eliminar_venta)
        btn_layout.addWidget(self.btn_eliminar)

        self.btn_refrescar = QPushButton("Actualizar Lista", self)
        self.btn_refrescar.clicked.connect(self.cargar_ventas)
        btn_layout.addWidget(self.btn_refrescar)

        layout.addLayout(btn_layout)

        # --- Tabla de ventas ---
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["ID", "Cliente", "Servicio", "Monto", "Fecha"])
        layout.addWidget(self.tabla)

        self.setLayout(layout)

        # Cargar datos al iniciar
        self.cargar_clientes_servicios()
        self.cargar_ventas()

    # ====================
    # MÉTODOS (CRD)
    # ====================

    def cargar_clientes_servicios(self):
        """Carga los clientes y servicios en los ComboBox"""
        self.cliente_id.clear()
        self.servicio_id.clear()

        # --- Clientes ---
        clientes = database.obtener_clientes()
        for c in clientes:
            self.cliente_id.addItem(f"{c[1]} (ID {c[0]})", c[0])  # texto visible, id oculto

        # --- Servicios ---
        servicios = database.obtener_servicios()
        for s in servicios:
            self.servicio_id.addItem(f"{s[1]} - ${s[2]} (ID {s[0]})", s[0])

    def registrar_venta(self):
        if self.cliente_id.currentIndex() < 0 or self.servicio_id.currentIndex() < 0:
            QMessageBox.warning(self, "Error", "Debes seleccionar cliente y servicio")
            return

        monto = self.monto.text().strip()
        if not monto:
            QMessageBox.warning(self, "Error", "El monto es obligatorio")
            return

        try:
            monto = float(monto)
        except ValueError:
            QMessageBox.warning(self, "Error", "El monto debe ser numérico")
            return

        cliente_id = self.cliente_id.currentData()
        servicio_id = self.servicio_id.currentData()

        database.registrar_venta(cliente_id, servicio_id, monto)
        QMessageBox.information(self, "Éxito", "Venta registrada")
        self.monto.clear()
        self.cargar_ventas()

    def eliminar_venta(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Error", "Selecciona una venta de la tabla")
            return

        venta_id = int(self.tabla.item(fila, 0).text())

        confirm = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Seguro que deseas eliminar la venta ID {venta_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            database.eliminar_venta(venta_id)
            QMessageBox.information(self, "Éxito", "Venta eliminada")
            self.cargar_ventas()

    def cargar_ventas(self):
        self.tabla.setRowCount(0)
        ventas = database.obtener_ventas()
        for row_num, row_data in enumerate(ventas):
            self.tabla.insertRow(row_num)
            for col_num, value in enumerate(row_data):
                self.tabla.setItem(row_num, col_num, QTableWidgetItem(str(value)))
