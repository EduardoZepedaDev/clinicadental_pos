# Clínica Dental POS 🦷💳

Sistema de punto de venta (POS) básico para clínica dental.  
Permite manejar clientes, servicios, ventas y generar tickets en impresora térmica **POS80**.  
También soporta exportación de datos a **Excel**.

---

## 🚀 Características
- **Clientes**: nombre, número telefónico.
- **Servicios**: nombre del servicio.
- **Ventas**: cliente, servicios múltiples, monto, folio automático, fecha.
- **Tickets**: impresión en impresora térmica **POS80 (80mm)**.
- **Reportes**: exportación a Excel (EPPlus/Pandas + OpenPyXL).

---

## 📦 Requisitos
- Python **3.11+**
- Librerías del archivo `requirements.txt`
- Impresora térmica configurada en Windows con nombre **POS80 Printer**

---

## ⚙️ Instalación
```bash
# Clonar repo
git clone https://github.com/EduardoZepedaDev/clinicadental_pos.git
cd clinicadental_pos

# Crear entorno virtual
python -m venv venv
# Activar
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
