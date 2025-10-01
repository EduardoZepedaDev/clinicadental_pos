from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QMessageBox, QTableWidget, QTableWidgetItem, QComboBox,
    QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QSizeF, QMarginsF
from PyQt6.QtGui import QPdfWriter, QTextDocument, QPageSize, QPageLayout
from PyQt6.QtPrintSupport import QPrinter
import database
import datetime
from pathlib import Path
import os

# Carpeta donde guardamos los tickets en PDF
SAVE_TICKETS_DIR = (Path(__file__).resolve().parent.parent / "tickets")
SAVE_TICKETS_DIR.mkdir(parents=True, exist_ok=True)

# Nombre exacto de tu impresora térmica en Windows
THERMAL_PRINTER_NAME = r"POS80 Printer"


class VentasWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clínica Dental POS · Ventas")
        self.setGeometry(400, 400, 780, 520)

        # Lista temporal de nombres de servicios seleccionados
        self.servicios_seleccionados = []

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # === Cliente (editable para crear rápido) ===
        self.cliente_id = QComboBox(self)
        self.cliente_id.setEditable(True)
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
        self.btn_agregar_serv.setObjectName("SecondaryButton")
        self.btn_agregar_serv.clicked.connect(self.agregar_servicio_a_lista)
        fila_busca.addWidget(self.btn_agregar_serv)

        layout.addLayout(fila_busca)

        # === Acciones de lista de servicios ===
        fila_acciones = QHBoxLayout()
        self.btn_quitar_sel = QPushButton("Quitar seleccionado", self)
        self.btn_quitar_sel.setObjectName("DangerButton")
        self.btn_quitar_sel.clicked.connect(self.quitar_servicio_seleccionado)
        fila_acciones.addWidget(self.btn_quitar_sel)

        self.btn_limpiar_serv = QPushButton("Limpiar servicios", self)
        self.btn_limpiar_serv.setObjectName("SecondaryButton")
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
        self.btn_guardar.setObjectName("PrimaryButton")
        self.btn_guardar.clicked.connect(self.registrar_venta)
        btn_layout.addWidget(self.btn_guardar)

        self.btn_eliminar = QPushButton("Eliminar Venta", self)
        self.btn_eliminar.setObjectName("DangerButton")
        self.btn_eliminar.clicked.connect(self.eliminar_venta)
        btn_layout.addWidget(self.btn_eliminar)

        layout.addLayout(btn_layout)

        # === Tabla de ventas ===
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["ID", "Cliente", "Servicios", "Monto", "Fecha"])
        self.tabla.setAlternatingRowColors(True)  # zebra
        layout.addWidget(self.tabla)

        # === Botón guardar ticket (desde selección) ===
        self.btn_imprimir = QPushButton("Guardar Ticket (PDF)")
        self.btn_imprimir.setObjectName("SecondaryButton")
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
        self.cliente_map = {c[0]: c[1] for c in clientes}
        for c in clientes:
            self.cliente_id.addItem(c[1], c[0])

        # Servicios
        self.servicio_id.clear()
        self.servicio_id.addItem("Selecciona Servicio", None)
        servicios = database.obtener_servicios()
        self.servicio_map = {s[0]: s[1] for s in servicios}
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

            # Generar ticket y mostrar opciones Ver/Imprimir
            self.imprimir_ticket_por_id(venta_id)

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
    # Guardado de Ticket (PDF) + Diálogo Ver/Imprimir
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

        # --- Diálogo con botones Ver PDF / Imprimir ---
        box = QMessageBox(self)
        box.setWindowTitle("Ticket generado")
        box.setText(f"Se guardó el ticket en:\n{pdf_path}")
        btn_ver = box.addButton("Ver PDF", QMessageBox.ButtonRole.ActionRole)
        btn_print = box.addButton("Imprimir", QMessageBox.ButtonRole.ActionRole)
        box.addButton("Cerrar", QMessageBox.ButtonRole.RejectRole)
        box.exec()

        clicked = box.clickedButton()
        if clicked == btn_ver:
            self._abrir_pdf(pdf_path)
        elif clicked == btn_print:
            # Imprime directo con Qt (sin ShellExecute)
            self._imprimir_ticket_qt(cliente_nombre, servicios_texto, float(monto), fecha)

    def _abrir_pdf(self, pdf_path: Path):
        """Abre el PDF con el visor predeterminado del sistema (Windows)."""
        try:
            os.startfile(str(pdf_path))  # Windows
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo abrir el PDF:\n{e}")

    def _imprimir_ticket_qt(self, cliente_nombre: str, servicios_texto: str, monto_total: float, fecha_txt: str):
        """Imprime el ticket directo a la impresora térmica usando QPrinter."""
        # Componer el mismo HTML que el PDF
        servicios_lista = [s.strip() for s in servicios_texto.split(",") if s.strip()]
        html = self._compose_ticket_html(cliente_nombre, fecha_txt, servicios_lista, monto_total)

        # Configurar impresora
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        if THERMAL_PRINTER_NAME:
            printer.setPrinterName(THERMAL_PRINTER_NAME)

        # Tamaño de ticket ~80x200 mm y márgenes
        page_size = QPageSize(QSizeF(80.0, 200.0), QPageSize.Unit.Millimeter)
        layout = printer.pageLayout()
        layout.setPageSize(page_size)
        layout.setOrientation(QPageLayout.Orientation.Portrait)
        layout.setMargins(QMarginsF(4, 6, 4, 6))
        printer.setPageLayout(layout)

        # Render del HTML
        doc = QTextDocument()
        doc.setHtml(html)
        paint_rect = layout.paintRectPoints()
        doc.setPageSize(QSizeF(paint_rect.width(), paint_rect.height()))

        try:
            doc.print(printer)
            QMessageBox.information(self, "Impresión", f"Ticket enviado a: {THERMAL_PRINTER_NAME or 'impresora predeterminada'}")
        except Exception as e:
            QMessageBox.warning(self, "Error de impresión", f"No se pudo imprimir:\n{e}")

    def _compose_ticket_html(self, cliente_nombre: str, fecha_txt: str, servicios_lista: list[str], monto_total: float) -> str:
        """Genera HTML compatible con QTextDocument (CSS básico)"""
        servicios_items = "\n".join(f"<li>{s}</li>" for s in servicios_lista)
        return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #111827; }}
  .wrap {{ width: 72mm; padding: 6mm; }}
  h1 {{ font-size: 14px; margin: 0 0 4px; text-align:center; color: #111827; }}
  .muted {{ color: #6B7280; font-size: 10px; text-align:center; }}
  .row {{ display: flex; justify-content: space-between; font-size: 11px; margin: 6px 0; }}
  .sep {{ border-top: 1px dashed #E5E7EB; margin: 8px 0; }}
  .title {{ font-weight: 600; margin: 8px 0 4px; font-size: 11px; }}
  ul {{ margin: 6px 0; padding-left: 14px; font-size: 11px; }}
  .total {{ font-weight: 700; font-size: 12px; }}
  .center {{ text-align: center; }}
</style>
</head>
<body>
  <div class="wrap">
    <h1>CLÍNICA DENTAL NORTE</h1>fecha_txt
    <div class="muted">31 Pte entre 6ª y 8ª Nte</div>
    <div class="muted">Col. 5 de Febrero</div>
    <div class="muted">Tel. 962 127 8373</div>
    <div class="muted">L–S 08:00–20:00</div>
    <div class="muted">RFC: GOMS6507062H3</div>
    <div class="row"><div><strong>Fecha</strong></div><div>{fecha_txt}</div></div>
    <div class="row"><div><strong>Cliente</strong></div><div>{cliente_nombre}</div></div>
    <div class="row"><div><strong>========================</strong></div></div>
    <div class="sep"></div>
    <div class="title">Servicios</div>
    <ul>
      {servicios_items}
    </ul>
    <div class="sep"></div>
    <div class="row"><div><strong>========================</strong></div></div>
    <div class="row total"><div>Total</div><div>${monto_total:,.2f}</div></div>

    <div class="sep"></div>

    <div class="center muted">¡Gracias por su preferencia!</div>
    <div class="center muted">clinica.odontologica.norte.85@gmail.com</div>
  </div>
</body>
</html>"""

    def generar_ticket_pdf(self, venta_id: int, cliente_nombre: str, servicios_texto: str,
                           monto_total: float, fecha_txt: str) -> Path:
        """
        Genera el PDF del ticket con HTML/CSS básico (QTextDocument + QPdfWriter) y lo guarda en /tickets:
        ticket_{ventaId}_{Cliente}_{yyyyMMdd}.pdf
        """
        # Nombre de archivo
        safe_cliente = "".join(ch if ch.isalnum() or ch in (" ", "_", "-") else "_" for ch in cliente_nombre)
        safe_cliente = "_".join(safe_cliente.split())
        fecha_archivo = datetime.datetime.now().strftime("%Y%m%d")
        filename = f"ticket_{venta_id}_{safe_cliente}_{fecha_archivo}.pdf"
        pdf_path = SAVE_TICKETS_DIR / filename

        # HTML
        servicios_lista = [s.strip() for s in servicios_texto.split(",") if s.strip()]
        html = self._compose_ticket_html(cliente_nombre, fecha_txt, servicios_lista, monto_total)

        # Writer con tamaño tipo ticket ~80mm x 200mm
        writer = QPdfWriter(str(pdf_path))
        page_size = QPageSize(QSizeF(80.0, 200.0), QPageSize.Unit.Millimeter)
        layout = QPageLayout(
            page_size,
            QPageLayout.Orientation.Portrait,
            QMarginsF(4, 6, 4, 6),
            QPageLayout.Unit.Millimeter
        )
        writer.setPageLayout(layout)

        # Render HTML
        doc = QTextDocument()
        doc.setHtml(html)

        # Área pintable (sin márgenes) con QSizeF
        paint_rect = layout.paintRectPoints()  # QRectF
        sizef = QSizeF(paint_rect.width(), paint_rect.height())
        doc.setPageSize(sizef)

        doc.print(writer)
        return pdf_path