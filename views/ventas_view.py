from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QMessageBox, QTableWidget, QTableWidgetItem, QComboBox,
    QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt
import database
import datetime
import os
import tempfile
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A7
from reportlab.lib.units import mm

# Carpeta donde guardamos los tickets en PDF
SAVE_TICKETS_DIR = (Path(__file__).resolve().parent.parent / "tickets")
SAVE_TICKETS_DIR.mkdir(parents=True, exist_ok=True)


class VentasWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Ventas")
        self.setGeometry(400, 400, 780, 520)

        # Lista temporal de nombres de servicios seleccionados
        self.servicios_seleccionados = []  # ["Limpieza", "Extracción", ...]

        layout = QVBoxLayout()

        # === Cliente (editable para crear rápido) ===
        self.cliente_id = QComboBox(self)
        self.cliente_id.setEditable(True)  # permite escribir un nombre nuevo
        self.cliente_id.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.cliente_id.setPlaceholderText("Selecciona o escribe un nuevo cliente")
        layout.addWidget(self.cliente_id)

        # === Buscador + selector de servicio ===
        fila_busca = QHBoxLayout()

        self.buscar_servicio = QLineEdit(self)
        self.buscar_servicio.setPlaceholderText("Buscar servicio...")
        fila_busca.addWidget(self.buscar_servicio)

        self.servicio_id = QComboBox(self)
        self.servicio_id.setPlaceholderText("Selecciona Servicio")
        fila_busca.addWidget(self.servicio_id)

        self.btn_agregar_serv = QPushButton("Agregar servicio", self)
        self.btn_agregar_serv.clicked.connect(self.agregar_servicio_a_lista)
        fila_busca.addWidget(self.btn_agregar_serv)

        layout.addLayout(fila_busca)

        # === Acciones de lista de servicios ===
        fila_acciones = QHBoxLayout()
        self.btn_quitar_sel = QPushButton("Quitar seleccionado", self)
        self.btn_quitar_sel.clicked.connect(self.quitar_servicio_seleccionado)
        fila_acciones.addWidget(self.btn_quitar_sel)

        self.btn_limpiar_serv = QPushButton("Limpiar servicios", self)
        self.btn_limpiar_serv.clicked.connect(self.limpiar_servicios)
        fila_acciones.addWidget(self.btn_limpiar_serv)

        fila_acciones.addStretch(1)
        layout.addLayout(fila_acciones)

        # === Lista de servicios elegidos ===
        self.lst_servicios = QListWidget(self)
        layout.addWidget(self.lst_servicios)

        # === Monto total ===
        self.monto = QLineEdit(self)
        self.monto.setPlaceholderText("Monto total (obligatorio)")
        layout.addWidget(self.monto)

        # === Botones ===
        btn_layout = QHBoxLayout()
        self.btn_guardar = QPushButton("Registrar Venta", self)
        self.btn_guardar.clicked.connect(self.registrar_venta)
        btn_layout.addWidget(self.btn_guardar)

        self.btn_eliminar = QPushButton("Eliminar Venta", self)
        self.btn_eliminar.clicked.connect(self.eliminar_venta)
        btn_layout.addWidget(self.btn_eliminar)

        layout.addLayout(btn_layout)

        # === Tabla de ventas ===
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["ID", "Cliente", "Servicios", "Monto", "Fecha"])
        layout.addWidget(self.tabla)

        # === Botón guardar ticket (desde selección) ===
        self.btn_imprimir = QPushButton("Guardar Ticket (PDF)")
        self.btn_imprimir.clicked.connect(self.imprimir_ticket_seleccionado)
        layout.addWidget(self.btn_imprimir)

        self.setLayout(layout)

        # Cargar datos
        self.cargar_clientes_servicios()
        self.buscar_servicio.textChanged.connect(self._filtrar_servicios_combo)
        self.cargar_ventas()

    # ====================
    # Helpers UI
    # ====================
    def cargar_clientes_servicios(self):
        # Clientes
        self.cliente_id.clear()
        self.cliente_id.addItem("Selecciona Cliente", None)

        clientes = database.obtener_clientes()
        self.cliente_map = {c[0]: c[1] for c in clientes}  # id -> nombre
        for c in clientes:
            self.cliente_id.addItem(c[1], c[0])

        # Servicios
        self.servicio_id.clear()
        self.servicio_id.addItem("Selecciona Servicio", None)
        servicios = database.obtener_servicios()
        self.servicio_map = {s[0]: s[1] for s in servicios}  # id -> nombre
        self._servicio_map_base = dict(self.servicio_map)
        for s in servicios:
            self.servicio_id.addItem(s[1], s[0])

    def _filtrar_servicios_combo(self):
        filtro = (self.buscar_servicio.text() or "").strip().lower()
        self.servicio_id.blockSignals(True)
        self.servicio_id.clear()
        self.servicio_id.addItem("Selecciona Servicio", None)

        if not filtro:
            for sid, nombre in self._servicio_map_base.items():
                self.servicio_id.addItem(nombre, sid)
            self.servicio_map = dict(self._servicio_map_base)
            self.servicio_id.blockSignals(False)
            return

        filtrados = {sid: nom for sid, nom in self._servicio_map_base.items() if filtro in nom.lower()}
        for sid, nombre in filtrados.items():
            self.servicio_id.addItem(nombre, sid)
        self.servicio_map = filtrados
        self.servicio_id.blockSignals(False)

    def agregar_servicio_a_lista(self):
        sid = self.servicio_id.currentData()
        if sid is None:
            QMessageBox.warning(self, "Error", "Selecciona un servicio válido.")
            return
        nombre = self.servicio_map.get(sid)
        if not nombre:
            return
        self.servicios_seleccionados.append(nombre)
        self.lst_servicios.addItem(QListWidgetItem(nombre))

    def quitar_servicio_seleccionado(self):
        row = self.lst_servicios.currentRow()
        if row >= 0:
            self.servicios_seleccionados.pop(row)
            self.lst_servicios.takeItem(row)

    def limpiar_servicios(self):
        self.servicios_seleccionados.clear()
        self.lst_servicios.clear()

    # ====================
    # CRUD Ventas
    # ====================
    def _asegurar_cliente(self):
        data = self.cliente_id.currentData()
        texto = (self.cliente_id.currentText() or "").strip()

        if data is not None:
            return data
        if not texto or texto == "Selecciona Cliente":
            return None

        try:
            database.agregar_cliente(texto, "")
        except Exception as ex:
            QMessageBox.warning(self, "Error", f"No se pudo crear el cliente:\n{ex}")
            return None

        clientes = database.obtener_clientes()
        if not clientes:
            return None
        nuevo_id = max(clientes, key=lambda r: r[0])[0]

        self.cargar_clientes_servicios()
        self._filtrar_servicios_combo()
        for idx in range(self.cliente_id.count()):
            if self.cliente_id.itemData(idx) == nuevo_id:
                self.cliente_id.setCurrentIndex(idx)
                break
        return nuevo_id

    def registrar_venta(self):
        cliente_id_sel = self._asegurar_cliente()
        if cliente_id_sel is None:
            QMessageBox.warning(self, "Error", "Selecciona o escribe un nombre de cliente.")
            return
        if not self.servicios_seleccionados:
            QMessageBox.warning(self, "Error", "Agrega al menos un servicio a la venta.")
            return

        monto_text = (self.monto.text() or "").strip()
        if not monto_text:
            QMessageBox.warning(self, "Error", "El monto total es obligatorio.")
            return
        try:
            monto_total = float(monto_text)
        except ValueError:
            QMessageBox.warning(self, "Error", "El monto debe ser numérico.")
            return

        try:
            venta_id = database.registrar_venta(cliente_id_sel, self.servicios_seleccionados, monto_total)
            QMessageBox.information(self, "Éxito", f"Venta #{venta_id} registrada.")

            # Guardar PDF del ticket
            self.imprimir_ticket_por_id(venta_id)

            # Limpiar UI
            self.limpiar_servicios()
            self.monto.clear()
            self.cliente_id.setCurrentIndex(0)
            self.servicio_id.setCurrentIndex(0)
            self.cargar_ventas()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo registrar la venta:\n{e}")

    def cargar_ventas(self):
        self.tabla.setRowCount(0)
        ventas = database.obtener_ventas()
        for row_num, row_data in enumerate(ventas):
            self.tabla.insertRow(row_num)
            for col_num, value in enumerate(row_data):
                self.tabla.setItem(row_num, col_num, QTableWidgetItem(str(value)))

    def eliminar_venta(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Error", "Selecciona una venta de la tabla.")
            return
        venta_id = int(self.tabla.item(fila, 0).text())
        nombre_cliente = self.tabla.item(fila, 1).text()
        confirm = QMessageBox.question(
            self, "Confirmar",
            f"¿Seguro que deseas eliminar la venta de {nombre_cliente}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            database.eliminar_venta(venta_id)
            QMessageBox.information(self, "Éxito", "Venta eliminada.")
            self.cargar_ventas()

    def imprimir_ticket_seleccionado(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Error", "Selecciona una venta para guardar su ticket.")
            return
        venta_id = int(self.tabla.item(fila, 0).text())
        self.imprimir_ticket_por_id(venta_id)

    # ====================
    # Guardado de Ticket (PDF)
    # ====================
    def imprimir_ticket_por_id(self, venta_id: int):
        venta = database.obtener_venta_por_id(venta_id)
        if not venta:
            QMessageBox.warning(self, "Error", "No se encontraron los datos de la venta.")
            return

        # venta: (id, cliente_id, servicios_texto, monto, fecha)
        _, cliente_id, servicios_texto, monto, fecha = venta
        cliente_nombre = self.cliente_map.get(cliente_id, "Desconocido")

        pdf_path = self.generar_ticket_pdf(
            venta_id=venta_id,
            cliente_nombre=cliente_nombre,
            servicios_texto=servicios_texto,
            monto_total=float(monto),
            fecha_txt=fecha
        )

        QMessageBox.information(
            self,
            "Ticket guardado",
            f"Se guardó el ticket en:\n{pdf_path}"
        )

    def generar_ticket_pdf(self, venta_id: int, cliente_nombre: str, servicios_texto: str,
                           monto_total: float, fecha_txt: str) -> Path:
        """
        Genera el PDF del ticket y lo guarda en /tickets con nombre:
        ticket_{ventaId}_{Cliente}_{yyyyMMdd}.pdf
        """
        # Sanitizar nombre del cliente para el archivo
        safe_cliente = "".join(ch if ch.isalnum() or ch in (" ", "_", "-") else "_" for ch in cliente_nombre)
        safe_cliente = "_".join(safe_cliente.split())
        fecha_archivo = datetime.datetime.now().strftime("%Y%m%d")
        filename = f"ticket_{venta_id}_{safe_cliente}_{fecha_archivo}.pdf"
        pdf_path = SAVE_TICKETS_DIR / filename

        try:
            c = canvas.Canvas(str(pdf_path), pagesize=A7)
            width, height = A7

            NOMBRE_TIENDA = "CLINICA DENTAL NORTE"
            DIRECCION_TIENDA = "31 PONIENTE ENTRE 6.ª y 8.ª NORTE COL. 5 DE FEBRERO"
            TELEFONO_TIENDA = "962 127 8373"
            EMAIL_TIENDA = "clinica.odontologica.norte.85@gmail.com"
            HORARIO_TIENDA = "L-S 08:00 AM a 08:00 PM"
            RFC_TIENDA = "GOMS6507062H3"

            y = height - 10 * mm
            lh = 4 * mm

            def draw_center(y_pos, text, font="Helvetica", size=8):
                c.setFont(font, size)
                tw = c.stringWidth(text, font, size)
                c.drawString((width - tw) / 2.0, y_pos, text)

            # Encabezado
            draw_center(y, NOMBRE_TIENDA.upper(), size=10); y -= lh
            draw_center(y, DIRECCION_TIENDA, size=7); y -= lh
            draw_center(y, TELEFONO_TIENDA, size=7); y -= lh
            draw_center(y, EMAIL_TIENDA, size=7); y -= lh
            draw_center(y, HORARIO_TIENDA, size=7); y -= lh
            draw_center(y, RFC_TIENDA, size=7); y -= lh * 1.5

            # Datos de venta
            c.setFont("Helvetica", 7)
            c.drawString(5 * mm, y, "FECHA:")
            c.drawRightString(width - 5 * mm, y, fecha_txt); y -= lh
            c.drawString(5 * mm, y, "CLIENTE:")
            c.drawRightString(width - 5 * mm, y, cliente_nombre); y -= lh * 1.5

            # Servicios
            c.drawString(5 * mm, y, "SERVICIOS:"); y -= lh * 0.5
            draw_center(y, "========================================", size=7); y -= lh * 0.5

            servicios_lista = [s.strip() for s in servicios_texto.split(",") if s.strip()]
            for nombre in servicios_lista:
                c.drawString(5 * mm, y, f"- {nombre}")
                y -= lh

            # Total
            draw_center(y, "========================================", size=7); y -= lh * 0.5
            c.drawString(5 * mm, y, "TOTAL:")
            c.drawRightString(width - 5 * mm, y, f"${float(monto_total):.2f}"); y -= lh * 2

            # Pie
            draw_center(y, "GRACIAS POR SU COMPRA", size=7); y -= lh
            draw_center(y, "clinicaodontologicanorte.com", size=7)

            c.showPage()
            c.save()

            return pdf_path

        except Exception as e:
            QMessageBox.warning(self, "Error al guardar PDF", f"No se pudo generar el ticket:\n{e}")
            # fallback temporal
            tmp = Path(tempfile.gettempdir()) / f"ticket_tmp_{venta_id}.pdf"
            return tmp
