from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QMessageBox, QTableWidget, QTableWidgetItem
)
import database


class ServiciosWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Servicios")
        self.setGeometry(350, 350, 500, 400)

        layout = QVBoxLayout()

        # --- Formulario ---
        self.nombre = QLineEdit(self)
        self.nombre.setPlaceholderText("Nombre del servicio")
        layout.addWidget(self.nombre)

        self.precio = QLineEdit(self)
        self.precio.setPlaceholderText("Precio")
        layout.addWidget(self.precio)

        # --- Botones ---
        btn_layout = QHBoxLayout()

        self.btn_guardar = QPushButton("Agregar Servicio", self)
        self.btn_guardar.clicked.connect(self.guardar_servicio)
        btn_layout.addWidget(self.btn_guardar)

        self.btn_eliminar = QPushButton("Eliminar Servicio", self)
        self.btn_eliminar.clicked.connect(self.eliminar_servicio)
        btn_layout.addWidget(self.btn_eliminar)

        self.btn_refrescar = QPushButton("Actualizar Lista", self)
        self.btn_refrescar.clicked.connect(self.cargar_servicios)
        btn_layout.addWidget(self.btn_refrescar)

        layout.addLayout(btn_layout)

        # --- Tabla de servicios ---
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Precio"])
        layout.addWidget(self.tabla)

        self.setLayout(layout)

        # Cargar datos al iniciar
        self.cargar_servicios()

    # ====================
    # MÉTODOS (CRD)
    # ====================

    def guardar_servicio(self):
        nombre = self.nombre.text().strip()
        precio = self.precio.text().strip()

        if not nombre or not precio:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios")
            return

        try:
            precio = float(precio)
        except ValueError:
            QMessageBox.warning(self, "Error", "El precio debe ser numérico")
            return

        database.agregar_servicio(nombre, precio)
        QMessageBox.information(self, "Éxito", "Servicio agregado")
        self.nombre.clear()
        self.precio.clear()
        self.cargar_servicios()

    def eliminar_servicio(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Error", "Selecciona un servicio de la tabla")
            return

        servicio_id = int(self.tabla.item(fila, 0).text())

        confirm = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Seguro que deseas eliminar el servicio ID {servicio_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            database.eliminar_servicio(servicio_id)
            QMessageBox.information(self, "Éxito", "Servicio eliminado")
            self.cargar_servicios()

    def cargar_servicios(self):
        self.tabla.setRowCount(0)
        servicios = database.obtener_servicios()
        for row_num, row_data in enumerate(servicios):
            self.tabla.insertRow(row_num)
            for col_num, value in enumerate(row_data):
                self.tabla.setItem(row_num, col_num, QTableWidgetItem(str(value)))
