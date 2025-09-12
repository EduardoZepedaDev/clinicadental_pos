from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QMessageBox, QTableWidget, QTableWidgetItem, QComboBox, QFileDialog
)
import database
import datetime
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A7 # A7 es un tamaño pequeño, similar a un ticket
from reportlab.lib.units import mm # Para trabajar con milímetros, más fácil para tickets
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont # Para registrar una fuente si es necesario


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
        
        # Campos para Pago y Cambio
        self.pago_con = QLineEdit(self)
        self.pago_con.setPlaceholderText("Pago con (opcional)")
        layout.addWidget(self.pago_con)
        
        self.cambio = QLineEdit(self)
        self.cambio.setPlaceholderText("Cambio")
        self.cambio.setReadOnly(True) # El cambio se calcula automáticamente
        layout.addWidget(self.cambio)

        # Conectar el cambio al monto pagado
        self.pago_con.textChanged.connect(self.calcular_cambio)
        self.monto.textChanged.connect(self.calcular_cambio) # También si cambia el monto total

        # --- Botones del formulario ---
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
        
        # --- Botón de imprimir ticket ---
        self.btn_imprimir = QPushButton("Imprimir Ticket", self)
        self.btn_imprimir.clicked.connect(self.imprimir_ticket_seleccionado)
        layout.addWidget(self.btn_imprimir)

        self.setLayout(layout)

        # Cargar datos al iniciar
        self.cargar_clientes_servicios()
        self.cargar_ventas()

    # ====================
    # MÉTODOS
    # ====================
    def calcular_cambio(self):
        try:
            total = float(self.monto.text()) if self.monto.text() else 0.0
            pago = float(self.pago_con.text()) if self.pago_con.text() else 0.0
            
            if pago >= total:
                cambio = pago - total
                self.cambio.setText(f"{cambio:.2f}")
            else:
                self.cambio.setText("") # Si no cubre el total, no hay cambio aún
        except ValueError:
            self.cambio.setText("Inválido")

    def cargar_clientes_servicios(self):
        """Carga los clientes y servicios en los ComboBox"""
        self.cliente_id.clear()
        self.servicio_id.clear()
        self.cliente_id.addItem("Selecciona Cliente", None) # Opción inicial
        self.servicio_id.addItem("Selecciona Servicio", None) # Opción inicial

        # --- Clientes ---
        clientes = database.obtener_clientes()
        self.cliente_map = {c[0]: c[1] for c in clientes}
        for c in clientes:
            self.cliente_id.addItem(f"{c[1]} (ID {c[0]})", c[0])

        # --- Servicios ---
        servicios = database.obtener_servicios()
        self.servicio_map = {s[0]: (s[1], s[2]) for s in servicios}
        for s in servicios:
            self.servicio_id.addItem(f"{s[1]} - ${s[2]} (ID {s[0]})", s[0])

    def registrar_venta(self):
        if self.cliente_id.currentData() is None or self.servicio_id.currentData() is None:
            QMessageBox.warning(self, "Error", "Debes seleccionar cliente y servicio válidos.")
            return

        monto_text = self.monto.text().strip()
        pago_text = self.pago_con.text().strip()
        cambio_text = self.cambio.text().strip()

        if not monto_text:
            QMessageBox.warning(self, "Error", "El monto total es obligatorio.")
            return

        try:
            monto_total = float(monto_text)
            pago_con = float(pago_text) if pago_text else 0.0
            cambio_calc = float(cambio_text) if cambio_text else 0.0
        except ValueError:
            QMessageBox.warning(self, "Error", "El monto y pago deben ser numéricos.")
            return

        if pago_con < monto_total:
            QMessageBox.warning(self, "Error", "El pago no cubre el monto total de la venta.")
            return

        cliente_id_sel = self.cliente_id.currentData()
        servicio_id_sel = self.servicio_id.currentData()

        database.registrar_venta(cliente_id_sel, servicio_id_sel, monto_total)
        QMessageBox.information(self, "Éxito", "Venta registrada.")
        
        # Llamamos a generar el PDF con todos los datos necesarios
        self.generar_ticket_pdf(cliente_id_sel, servicio_id_sel, monto_total, pago_con, cambio_calc)
        
        # Limpiar campos después de registrar
        self.monto.clear()
        self.pago_con.clear()
        self.cambio.clear()
        self.cliente_id.setCurrentIndex(0)
        self.servicio_id.setCurrentIndex(0)
        self.cargar_ventas()

    def eliminar_venta(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Error", "Selecciona una venta de la tabla.")
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
            QMessageBox.information(self, "Éxito", "Venta eliminada.")
            self.cargar_ventas()

    def cargar_ventas(self):
        self.tabla.setRowCount(0)
        ventas = database.obtener_ventas()
        for row_num, row_data in enumerate(ventas):
            self.tabla.insertRow(row_num)
            for col_num, value in enumerate(row_data):
                self.tabla.setItem(row_num, col_num, QTableWidgetItem(str(value)))
                
    def imprimir_ticket_seleccionado(self):
        """Genera un ticket PDF para la venta seleccionada en la tabla."""
        fila_seleccionada = self.tabla.currentRow()
        if fila_seleccionada < 0:
            QMessageBox.warning(self, "Error", "Debes seleccionar una venta de la tabla para imprimir.")
            return

        venta_id = int(self.tabla.item(fila_seleccionada, 0).text())
        
        # Obtener los datos de la venta de la base de datos
        venta_data = database.obtener_venta_por_id(venta_id)
        
        if not venta_data:
            QMessageBox.warning(self, "Error", "No se encontraron los datos de la venta.")
            return
            
        # Desempaquetar los datos de la venta
        id, cliente_id, servicio_id, monto, fecha = venta_data
        
        # Para la reimpresión, asumimos que el pago fue igual al monto
        self.generar_ticket_pdf(cliente_id, servicio_id, monto, monto, 0.0)
        
        QMessageBox.information(self, "Ticket Impreso", f"Se ha generado el ticket PDF de la venta ID {id}.")
                
    def generar_ticket_pdf(self, cliente_id, servicio_id, monto_total, pago_con, cambio_calc):
        """Genera un ticket de venta en formato PDF con estilo de impresora térmica."""
        
        # Obtiene la ruta donde se guardará el archivo
        file_name, _ = QFileDialog.getSaveFileName(
            self, 
            "Guardar Ticket PDF", 
            os.path.join(os.getcwd(), f"ticket_venta_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"),
            "PDF Files (*.pdf)"
        )
        
        if not file_name:
            return # El usuario canceló la operación

        try:
            # Creamos un lienzo (canvas) con un tamaño pequeño para el ticket (ej. A7)
            c = canvas.Canvas(file_name, pagesize=A7) 
            width, height = A7 # Obtener el ancho y alto de la página

            # --- Datos de la tienda ---
            NOMBRE_TIENDA = "CLINICA DENTAL NORTE"
            DIRECCION_TIENDA = "31 PONIENTE ENTRE 6.ª y 8.ª NORTE COL. 5 DE FEBRERO"
            TELEFONO_TIENDA = "962 127 8373"
            EMAIL_TIENDA = "clinica.odontologica.norte.85@gmail.com"
            HORARIO_TIENDA = "L-S 08:00 AM a 08:00 PM"
            RFC_TIENDA = "GOMS6507062H3" # RFC (puedes cambiarlo)

            # --- Información del cliente y servicio ---
            nombre_cliente = self.cliente_map.get(cliente_id, 'Desconocido')
            nombre_servicio, precio_servicio = self.servicio_map.get(servicio_id, ('Desconocido', 0.0))
            
            # --- Empezamos a dibujar en el PDF ---
            y_offset = height - 10*mm # Punto de inicio desde la parte superior (en mm)
            line_height = 4*mm # Altura de cada línea (espaciado)

            # Centrar textos
            def draw_centered_text(y_pos, text, font_name="Helvetica", font_size=8):
                c.setFont(font_name, font_size)
                text_width = c.stringWidth(text, font_name, font_size)
                c.drawString((width - text_width) / 2.0, y_pos, text)

            # --- Encabezado de la tienda ---
            draw_centered_text(y_offset, NOMBRE_TIENDA.upper(), font_size=10)
            y_offset -= line_height
            draw_centered_text(y_offset, DIRECCION_TIENDA, font_size=7)
            y_offset -= line_height
            draw_centered_text(y_offset, TELEFONO_TIENDA, font_size=7)
            y_offset -= line_height
            draw_centered_text(y_offset, EMAIL_TIENDA, font_size=7)
            y_offset -= line_height
            draw_centered_text(y_offset, HORARIO_TIENDA, font_size=7)
            y_offset -= line_height
            draw_centered_text(y_offset, RFC_TIENDA, font_size=7)
            y_offset -= line_height * 1.5 # Más espacio

            # --- Datos del ticket ---
            c.setFont("Helvetica", 7)
            
            # Formatear la fecha y hora
            fecha_hora_str = datetime.datetime.now().strftime('%d/%m/%Y %H:%M %p').replace('AM', 'am').replace('PM', 'pm')
            
            c.drawString(5*mm, y_offset, "FECHA:")
            c.drawString(width - c.stringWidth(fecha_hora_str, "Helvetica", 7) - 5*mm, y_offset, fecha_hora_str)
            y_offset -= line_height
            
            # --- Cliente ---
            c.drawString(5*mm, y_offset, "CLIENTE:")
            c.drawString(width - c.stringWidth(nombre_cliente, "Helvetica", 7) - 5*mm, y_offset, nombre_cliente)
            y_offset -= line_height * 1.5

            # --- Encabezado de la tabla de artículos ---
            c.drawString(5*mm, y_offset, "CANT. DESCRIPCIÓN")
            y_offset -= line_height * 0.5 # Menos espacio
            draw_centered_text(y_offset, "========================================", font_size=7)
            y_offset -= line_height * 0.5

            # --- Detalle del servicio ---
            cantidad_servicio = 1 
            max_desc_width = width - 10*mm - c.stringWidth(f"${precio_servicio:.2f}", "Helvetica", 7) - 5*mm
            desc_text = f"{cantidad_servicio} {nombre_servicio}"
            if c.stringWidth(desc_text, "Helvetica", 7) > max_desc_width:
                 desc_text = desc_text[:int(len(desc_text) * (max_desc_width / c.stringWidth(desc_text, "Helvetica", 7)))] + "..."

            c.drawString(5*mm, y_offset, desc_text)
            c.drawRightString(width - 5*mm, y_offset, f"${precio_servicio:.2f}")
            y_offset -= line_height * 1.5 

            # --- Totales ---
            draw_centered_text(y_offset, "========================================", font_size=7)
            y_offset -= line_height * 0.5

            # Número de artículos (solo 1 en este ejemplo simplificado)
            c.drawString(5*mm, y_offset, f"NO. DE ARTICULOS: {cantidad_servicio}") 
            y_offset -= line_height

            c.drawString(width - c.stringWidth("TOTAL:", "Helvetica", 7) - c.stringWidth(f"${monto_total:.2f}", "Helvetica", 7) - 10*mm, y_offset, "TOTAL:")
            c.drawRightString(width - 5*mm, y_offset, f"${monto_total:.2f}")
            y_offset -= line_height

            c.drawString(width - c.stringWidth("PAGO CON:", "Helvetica", 7) - c.stringWidth(f"${pago_con:.2f}", "Helvetica", 7) - 10*mm, y_offset, "PAGO CON:")
            c.drawRightString(width - 5*mm, y_offset, f"${pago_con:.2f}")
            y_offset -= line_height

            c.drawString(width - c.stringWidth("SU CAMBIO:", "Helvetica", 7) - c.stringWidth(f"${cambio_calc:.2f}", "Helvetica", 7) - 10*mm, y_offset, "SU CAMBIO:")
            c.drawRightString(width - 5*mm, y_offset, f"${cambio_calc:.2f}")
            y_offset -= line_height * 2 # Más espacio

            # --- Pie de página ---
            draw_centered_text(y_offset, "GRACIAS POR SU COMPRA", font_size=7)
            y_offset -= line_height
            draw_centered_text(y_offset, "clinicaodontologicanorte.com", font_size=7) # Puedes cambiar por tu URL
            
            c.showPage() # Finaliza la página
            c.save() # Guarda el PDF
            
            QMessageBox.information(self, "Éxito", f"Ticket PDF guardado en:\n{file_name}")

        except Exception as e:
            QMessageBox.warning(self, "Error al generar PDF", f"No se pudo generar el ticket PDF: {e}")