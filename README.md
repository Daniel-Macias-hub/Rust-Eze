# Rust-Eze Agency – Sistema de Gestión de Ventas de Autos

> Calidad, antes que cantidad

Sistema de gestión para una agencia de venta de automóviles con backend en **Flask**, frontend en **Bootstrap 5** y base de datos **SQL Server 2022**.

---

## Características principales

### Arquitectura

- **Backend:** Flask con Blueprints (admin, auth, client)
- **Frontend:** Bootstrap 5 + JavaScript vanilla
- **Base de datos:** SQL Server 2022 Express
- **Autenticación:** Roles separados (Administrador / Cliente)
- **Patrón de configuración:** Archivo `config.py` centralizado

### Funcionalidades de administrador

- Dashboard con:
  - Conteo de vehículos en inventario
  - Número de clientes activos
  - Número de ventas realizadas
  - Suma total de ingresos
  - Gráfica de ventas por mes (Chart.js)
  - Top de modelos más vendidos
- Gestión completa de vehículos:
  - Alta, edición, baja lógica
  - Campos como marca, modelo, año, tipo, color, precio, estado, imagen, etc.
- Gestión de clientes:
  - Registro manual desde el panel de admin
  - Activación / desactivación de clientes
- Gestión de empleados:
  - Registro, edición y baja lógica
  - Asociación de ventas a empleados
- Gestión de ventas:
  - Registro de nuevas ventas desde el panel
  - Detalle de cada venta con cliente, vehículo, empleado y total

### Funcionalidades de cliente

- Panel de cliente con diseño oscuro y tarjetas de acción:
  - Explorar catálogo
  - Acceso a perfil
- Catálogo de vehículos:
  - Filtros por marca, modelo, año, tipo y rango de precio
  - Tarjetas con imagen, descripción y precio
  - Botón **“Comprar ahora”** que registra la venta en el sistema
- Sección de “Coches populares” (vehículos destacados)
- Página de perfil de cliente (`/client/perfil`) para ver y ajustar datos básicos

### Base de datos

- Tablas principales:
  - `Clientes`, `Empleados`, `Vehiculos`, `Ventas`, `Detalle_Ventas`
- Integridad referencial con claves foráneas
- Triggers de auditoría (altas, bajas y cambios)
- Procedimientos almacenados para operaciones de negocio
- Índices para acelerar consultas de búsqueda

---

## Tecnologías utilizadas

- **Backend:**
  - Python 3.10+
  - Flask
- **Frontend:**
  - HTML5, CSS3
  - Bootstrap 5
  - Font Awesome
  - Chart.js
- **Base de datos:**
  - SQL Server 2022 Express
  - ODBC Driver 17 for SQL Server
- **Otros:**
  - Git / GitHub
  - Entorno virtual con `venv`

---

## Instalación rápida (entorno local)

### 1. Clonar el repositorio

```bash
git clone https://github.com/Daniel-Macias-hub/Rust-Eze.git
cd Rust-Eze
------------------------------------------------------------------------------------------------------------
# Crear entorno virtual (Windows)
python -m venv .venv
------------------------------------------------------------------------------------------------------------
# Activar
.venv\Scripts\activate
------------------------------------------------------------------------------------------------------------
Instalar dependencias
pip install -r requirements.txt
------------------------------------------------------------------------------------------------------------
Ejecutar la aplicación
python app.py
------------------------------------------------------------------------------------------------------------
La aplicación quedará disponible en:
http://127.0.0.1:5000