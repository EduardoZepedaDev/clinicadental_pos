from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QMessageBox, QTableWidget, QTableWidgetItem
)
import database


class ClientesWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Clientes")
        self.setGeometry(300, 300, 500, 400)

        layout = QVBoxLayout()

        # --- Formulario ---
        self.nombre = QLineEdit(self)
        self.nombre.setPlaceholderText("Nombre del cliente")
        layout.addWidget(self.nombre)

        self.telefono = QLineEdit(self)
        self.telefono.setPlaceholderText("Teléfono")
        layout.addWidget(self.telefono)

        # --- Botones ---
        btn_layout = QHBoxLayout()

        self.btn_guardar = QPushButton("Agregar Cliente", self)
        self.btn_guardar.clicked.connect(self.guardar_cliente)
        btn_layout.addWidget(self.btn_guardar)

        self.btn_eliminar = QPushButton("Eliminar Cliente", self)
        self.btn_eliminar.clicked.connect(self.eliminar_cliente)
        btn_layout.addWidget(self.btn_eliminar)

        layout.addLayout(btn_layout)

        # --- Tabla de clientes ---
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Teléfono"])
        layout.addWidget(self.tabla)

        self.setLayout(layout)

        # Cargar datos al iniciar
        self.cargar_clientes()

    # ====================
    # MÉTODOS (CRD)
    # ====================

    def guardar_cliente(self):
        nombre = self.nombre.text().strip()
        telefono = self.telefono.text().strip()

        if not nombre or not telefono:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios")
            return

        database.agregar_cliente(nombre, telefono)
        QMessageBox.information(self, "Éxito", "Cliente agregado")
        self.nombre.clear()
        self.telefono.clear()
        self.cargar_clientes()

    def eliminar_cliente(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Error", "Selecciona un cliente de la tabla")
            return

        cliente_id = int(self.tabla.item(fila, 0).text())
        nombre_cliente = self.tabla.item(fila, 1).text()
        confirm = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Seguro que deseas eliminar al cliente {nombre_cliente}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            database.eliminar_cliente(cliente_id)
            QMessageBox.information(self, "Éxito", "Cliente eliminado")
            self.cargar_clientes()

    def cargar_clientes(self):
        self.tabla.setRowCount(0)
        clientes = database.obtener_clientes()
        for row_num, row_data in enumerate(clientes):
            self.tabla.insertRow(row_num)
            for col_num, value in enumerate(row_data):
                self.tabla.setItem(row_num, col_num, QTableWidgetItem(str(value)))
