import win32print
import win32ui
from datetime import datetime

def print_ticket(cliente, servicio, monto):
    printer_name = "EPSON TM-T88V Receipt"  # Ajusta al nombre real de la impresora instalada
    hprinter = win32print.OpenPrinter(printer_name)
    hdc = win32print.CreateDC("WINSPOOL", printer_name, None)

    hdc.StartDoc("Ticket")
    hdc.StartPage()

    text = f"""
    CLINICA DENTAL
    -----------------------------
    Cliente: {cliente}
    Servicio: {servicio}
    Monto: ${monto:.2f}
    Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M")}
    -----------------------------
    ¡Gracias por su visita!
    """

    hdc.TextOut(50, 50, text)
    hdc.EndPage()
    hdc.EndDoc()
    win32print.ClosePrinter(hprinter)
