from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    abort,
)
from functools import wraps
from utils.database import execute_query, call_stored_procedure, User

# Blueprint único para admin
admin_bp = Blueprint("admin", __name__)


# ============================
# Helper: solo administradores
# ============================
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("es_administrador"):
            flash("Acceso restringido a administradores.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return wrapper


# ============================
# Dashboard
# ============================
@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    stats = {}

    # Conteos básicos
    stats["vehiculos"] = execute_query(
        "SELECT COUNT(*) AS total FROM Vehiculos"
    )[0]["total"]

    stats["clientes"] = execute_query(
        "SELECT COUNT(*) AS total FROM Clientes WHERE activo = 1"
    )[0]["total"]

    stats["ventas"] = execute_query(
        "SELECT COUNT(*) AS total FROM Ventas"
    )[0]["total"]

    # Ingresos totales (puede ser NULL si no hay ventas)
    row_ingresos = execute_query(
        "SELECT SUM(total_venta) AS total FROM Ventas"
    )[0]
    stats["total_ingresos"] = row_ingresos["total"] or 0

    # Ventas recientes para la tabla
    ventas_recientes = execute_query(
        """
        SELECT TOP 10
            v.venta_id,
            v.fecha_venta,
            v.total_venta,
            v.metodo_pago,
            v.estado_venta,
            c.nombre_completo AS cliente,
            e.nombre_completo AS empleado
        FROM Ventas v
        JOIN Clientes c ON v.cliente_id = c.cliente_id
        JOIN Empleados e ON v.empleado_id = e.empleado_id
        ORDER BY v.fecha_venta DESC
        """
    )

    # Datos agregados para Chart.js: ventas por mes (últimos 12 meses)
    ventas_por_mes = execute_query(
        """
        SELECT
            FORMAT(v.fecha_venta, 'yyyy-MM') AS periodo,
            SUM(v.total_venta) AS total
        FROM Ventas v
        GROUP BY FORMAT(v.fecha_venta, 'yyyy-MM')
        ORDER BY periodo
        """
    )
    ventas_por_mes_labels = [row["periodo"] for row in ventas_por_mes]
    ventas_por_mes_valores = [float(row["total"]) for row in ventas_por_mes]

    # Top 5 modelos vendidos
    top_modelos = execute_query(
        """
        SELECT TOP 5
            CONCAT(ve.marca, ' ', ve.modelo, ' ', ve.anio) AS etiqueta,
            COUNT(*) AS unidades
        FROM Ventas v
        JOIN Detalle_Ventas dv ON v.venta_id = dv.venta_id
        JOIN Vehiculos ve      ON dv.vehiculo_id = ve.vehiculo_id
        GROUP BY ve.marca, ve.modelo, ve.anio
        ORDER BY unidades DESC
        """
    )
    top_modelos_labels = [row["etiqueta"] for row in top_modelos]
    top_modelos_valores = [int(row["unidades"]) for row in top_modelos]

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        ventas_recientes=ventas_recientes,
        ventas_por_mes_labels=ventas_por_mes_labels,
        ventas_por_mes_valores=ventas_por_mes_valores,
        top_modelos_labels=top_modelos_labels,
        top_modelos_valores=top_modelos_valores,
    )

# ============================
# CRUD VEHÍCULOS
# ============================
@admin_bp.route("/vehiculos")
@admin_required
def vehiculos_list():
    vehiculos = execute_query(
        """
        SELECT vehiculo_id, marca, modelo, anio, precio, color, tipo,
               estado_disponibilidad, fecha_ingreso
        FROM Vehiculos
        ORDER BY fecha_ingreso DESC, vehiculo_id DESC
    """
    )
    return render_template("admin/vehiculos/list.html", vehiculos=vehiculos)


@admin_bp.route("/vehiculos/nuevo", methods=["GET", "POST"])
@admin_required
def vehiculos_nuevo():
    if request.method == "POST":
        marca = request.form.get("marca")
        modelo = request.form.get("modelo")
        anio = request.form.get("anio", type=int)
        precio = request.form.get("precio", type=float)
        color = request.form.get("color")
        tipo = request.form.get("tipo")
        estado = request.form.get("estado_disponibilidad", "Disponible")
        descripcion = request.form.get("descripcion")
        imagen_url = request.form.get("imagen_url")

        if not all([marca, modelo, anio, precio, color, tipo]):
            flash(
                "Marca, modelo, año, precio, color y tipo son obligatorios.", "danger"
            )
            return render_template(
                "admin/vehiculos/form.html", modo="nuevo", vehiculo=request.form
            )

        execute_query(
            """
            INSERT INTO Vehiculos
                (marca, modelo, anio, precio, color, tipo,
                 estado_disponibilidad, descripcion, imagen_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (marca, modelo, anio, precio, color, tipo, estado, descripcion, imagen_url),
            fetch=False,
        )

        flash("Vehículo creado correctamente.", "success")
        return redirect(url_for("admin.vehiculos_list"))

    return render_template("admin/vehiculos/form.html", modo="nuevo", vehiculo=None)


@admin_bp.route("/vehiculos/<int:vehiculo_id>/editar", methods=["GET", "POST"])
@admin_required
def vehiculos_editar(vehiculo_id):
    if request.method == "POST":
        marca = request.form.get("marca")
        modelo = request.form.get("modelo")
        anio = request.form.get("anio", type=int)
        precio = request.form.get("precio", type=float)
        color = request.form.get("color")
        tipo = request.form.get("tipo")
        estado = request.form.get("estado_disponibilidad", "Disponible")
        descripcion = request.form.get("descripcion")
        imagen_url = request.form.get("imagen_url")

        if not all([marca, modelo, anio, precio, color, tipo]):
            flash(
                "Marca, modelo, año, precio, color y tipo son obligatorios.", "danger"
            )
            return redirect(
                url_for("admin.vehiculos_editar", vehiculo_id=vehiculo_id)
            )

        execute_query(
            """
            UPDATE Vehiculos
            SET marca = ?, modelo = ?, anio = ?, precio = ?,
                color = ?, tipo = ?, estado_disponibilidad = ?,
                descripcion = ?, imagen_url = ?
            WHERE vehiculo_id = ?
        """,
            (
                marca,
                modelo,
                anio,
                precio,
                color,
                tipo,
                estado,
                descripcion,
                imagen_url,
                vehiculo_id,
            ),
            fetch=False,
        )

        flash("Vehículo actualizado correctamente.", "success")
        return redirect(url_for("admin.vehiculos_list"))

    rows = execute_query(
        "SELECT * FROM Vehiculos WHERE vehiculo_id = ?", (vehiculo_id,)
    )
    if not rows:
        flash("Vehículo no encontrado.", "warning")
        return redirect(url_for("admin.vehiculos_list"))

    return render_template(
        "admin/vehiculos/form.html", modo="editar", vehiculo=rows[0]
    )


@admin_bp.route("/vehiculos/<int:vehiculo_id>/eliminar", methods=["POST"])
@admin_required
def vehiculos_eliminar(vehiculo_id):
    try:
        execute_query(
            "DELETE FROM Vehiculos WHERE vehiculo_id = ?",
            (vehiculo_id,),
            fetch=False,
        )
        flash("Vehículo eliminado correctamente.", "success")
    except Exception as e:
        # En caso de FK (vehículo con ventas)
        flash(f"No se pudo eliminar el vehículo: {e}", "danger")
    return redirect(url_for("admin.vehiculos_list"))


# ============================
# CRUD CLIENTES
# ============================
@admin_bp.route("/clientes")
@admin_required
def clientes_list():
    clientes = execute_query(
        """
        SELECT cliente_id, nombre_completo, email, telefono,
               direccion, tipo_documento, numero_documento,
               activo, fecha_registro
        FROM Clientes
        ORDER BY cliente_id DESC
    """
    )
    return render_template("admin/clientes/list.html", clientes=clientes)


@admin_bp.route("/clientes/nuevo", methods=["GET", "POST"])
@admin_required
def clientes_nuevo():
    if request.method == "POST":
        nombre = request.form.get("nombre_completo")
        email = request.form.get("email")
        telefono = request.form.get("telefono")
        direccion = request.form.get("direccion")
        tipo_doc = request.form.get("tipo_documento") or "INE"
        num_doc = request.form.get("numero_documento") or "POR_ASIGNAR"
        password = request.form.get("password")

        if not all([nombre, email, password]):
            flash("Nombre, email y contraseña son obligatorios.", "danger")
            return render_template(
                "admin/clientes/form.html", modo="nuevo", cliente=request.form
            )

        password_hash = User.hash_password(password)

        execute_query(
            """
            INSERT INTO Clientes
                (nombre_completo, email, telefono, direccion,
                 tipo_documento, numero_documento, password_hash, activo)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """,
            (nombre, email, telefono, direccion, tipo_doc, num_doc, password_hash),
            fetch=False,
        )

        flash("Cliente creado correctamente.", "success")
        return redirect(url_for("admin.clientes_list"))

    return render_template("admin/clientes/form.html", modo="nuevo", cliente=None)


@admin_bp.route("/clientes/<int:cliente_id>/editar", methods=["GET", "POST"])
@admin_required
def clientes_editar(cliente_id):
    if request.method == "POST":
        nombre = request.form.get("nombre_completo")
        email = request.form.get("email")
        telefono = request.form.get("telefono")
        direccion = request.form.get("direccion")
        tipo_doc = request.form.get("tipo_documento") or "INE"
        num_doc = request.form.get("numero_documento") or "POR_ASIGNAR"
        activo = 1 if request.form.get("activo") == "1" else 0
        password = request.form.get("password")

        if not all([nombre, email]):
            flash("Nombre y email son obligatorios.", "danger")
            return redirect(url_for("admin.clientes_editar", cliente_id=cliente_id))

        execute_query(
            """
            UPDATE Clientes
            SET nombre_completo = ?, email = ?, telefono = ?, direccion = ?,
                tipo_documento = ?, numero_documento = ?, activo = ?
            WHERE cliente_id = ?
        """,
            (nombre, email, telefono, direccion, tipo_doc, num_doc, activo, cliente_id),
            fetch=False,
        )

        if password:
            password_hash = User.hash_password(password)
            execute_query(
                """
                UPDATE Clientes
                SET password_hash = ?
                WHERE cliente_id = ?
            """,
                (password_hash, cliente_id),
                fetch=False,
            )

        flash("Cliente actualizado correctamente.", "success")
        return redirect(url_for("admin.clientes_list"))

    rows = execute_query("SELECT * FROM Clientes WHERE cliente_id = ?", (cliente_id,))
    if not rows:
        flash("Cliente no encontrado.", "warning")
        return redirect(url_for("admin.clientes_list"))

    return render_template(
        "admin/clientes/form.html", modo="editar", cliente=rows[0]
    )


@admin_bp.route("/clientes/<int:cliente_id>/eliminar", methods=["POST"])
@admin_required
def clientes_eliminar(cliente_id):
    # Baja lógica para no romper FKs
    execute_query(
        """
        UPDATE Clientes
        SET activo = 0
        WHERE cliente_id = ?
    """,
        (cliente_id,),
        fetch=False,
    )

    flash("Cliente desactivado correctamente.", "info")
    return redirect(url_for("admin.clientes_list"))


# ============================
# CRUD EMPLEADOS
# ============================
@admin_bp.route("/empleados")
@admin_required
def empleados_list():
    empleados = execute_query(
        """
        SELECT empleado_id, nombre_completo, email, puesto,
               es_administrador, activo, fecha_contratacion
        FROM Empleados
        ORDER BY empleado_id DESC
    """
    )
    return render_template("admin/empleados/list.html", empleados=empleados)


@admin_bp.route("/empleados/nuevo", methods=["GET", "POST"])
@admin_required
def empleados_nuevo():
    if request.method == "POST":
        nombre = request.form.get("nombre_completo")
        email = request.form.get("email")
        puesto = request.form.get("puesto")
        password = request.form.get("password")
        es_admin = 1 if request.form.get("es_administrador") == "1" else 0

        if not all([nombre, email, puesto, password]):
            flash("Nombre, email, puesto y contraseña son obligatorios.", "danger")
            return render_template(
                "admin/empleados/form.html", modo="nuevo", empleado=request.form
            )

        password_hash = User.hash_password(password)

        execute_query(
            """
            INSERT INTO Empleados
                (nombre_completo, email, puesto, password_hash,
                 es_administrador, activo)
            VALUES (?, ?, ?, ?, ?, 1)
        """,
            (nombre, email, puesto, password_hash, es_admin),
            fetch=False,
        )

        flash("Empleado creado correctamente.", "success")
        return redirect(url_for("admin.empleados_list"))

    return render_template("admin/empleados/form.html", modo="nuevo", empleado=None)


@admin_bp.route("/empleados/<int:empleado_id>/editar", methods=["GET", "POST"])
@admin_required
def empleados_editar(empleado_id):
    if request.method == "POST":
        nombre = request.form.get("nombre_completo")
        email = request.form.get("email")
        puesto = request.form.get("puesto")
        activo = 1 if request.form.get("activo") == "1" else 0
        es_admin = 1 if request.form.get("es_administrador") == "1" else 0
        password = request.form.get("password")  # opcional

        if not all([nombre, email, puesto]):
            flash("Nombre, email y puesto son obligatorios.", "danger")
            return redirect(
                url_for("admin.empleados_editar", empleado_id=empleado_id)
            )

        execute_query(
            """
            UPDATE Empleados
            SET nombre_completo = ?, email = ?, puesto = ?,
                es_administrador = ?, activo = ?
            WHERE empleado_id = ?
        """,
            (nombre, email, puesto, es_admin, activo, empleado_id),
            fetch=False,
        )

        if password:
            password_hash = User.hash_password(password)
            execute_query(
                """
                UPDATE Empleados
                SET password_hash = ?
                WHERE empleado_id = ?
            """,
                (password_hash, empleado_id),
                fetch=False,
            )

        flash("Empleado actualizado correctamente.", "success")
        return redirect(url_for("admin.empleados_list"))

    rows = execute_query(
        """
        SELECT empleado_id, nombre_completo, email, puesto,
               es_administrador, activo
        FROM Empleados
        WHERE empleado_id = ?
    """,
        (empleado_id,),
    )

    if not rows:
        flash("Empleado no encontrado.", "warning")
        return redirect(url_for("admin.empleados_list"))

    return render_template(
        "admin/empleados/form.html", modo="editar", empleado=rows[0]
    )


@admin_bp.route("/empleados/<int:empleado_id>/eliminar", methods=["POST"])
@admin_required
def empleados_eliminar(empleado_id):
    # Baja lógica para no romper FKs en Ventas
    execute_query(
        """
        UPDATE Empleados
        SET activo = 0
        WHERE empleado_id = ?
    """,
        (empleado_id,),
        fetch=False,
    )

    flash("Empleado desactivado correctamente.", "info")
    return redirect(url_for("admin.empleados_list"))


# ============================
# VENTAS (listar / detalle / cancelar)
# ============================
@admin_bp.route("/ventas")
@admin_required
def ventas_list():
    ventas = execute_query(
        """
        SELECT 
            v.venta_id,
            v.fecha_venta,
            v.total_venta,
            v.metodo_pago,
            v.estado_venta,
            c.nombre_completo AS cliente,
            e.nombre_completo AS empleado
        FROM Ventas v
        JOIN Clientes c ON v.cliente_id = c.cliente_id
        JOIN Empleados e ON v.empleado_id = e.empleado_id
        ORDER BY v.fecha_venta DESC
    """
    )
    return render_template("admin/ventas/list.html", ventas=ventas)


@admin_bp.route("/ventas/<int:venta_id>")
@admin_required
def ventas_detail(venta_id):
    rows = execute_query(
        """
        SELECT TOP 1
            v.venta_id,
            v.fecha_venta,
            v.total_venta,
            v.metodo_pago,
            v.estado_venta,
            c.nombre_completo AS cliente,
            c.email           AS cliente_email,
            e.nombre_completo AS empleado,
            e.email           AS empleado_email,
            ve.marca,
            ve.modelo,
            ve.anio,
            ve.color,
            ve.tipo
        FROM Ventas v
        JOIN Detalle_Ventas dv ON v.venta_id = dv.venta_id
        JOIN Vehiculos ve      ON dv.vehiculo_id = ve.vehiculo_id
        JOIN Clientes c        ON v.cliente_id = c.cliente_id
        JOIN Empleados e       ON v.empleado_id = e.empleado_id
        WHERE v.venta_id = ?
    """,
        (venta_id,),
    )

    if not rows:
        flash("Venta no encontrada.", "warning")
        return redirect(url_for("admin.ventas_list"))

    venta = rows[0]
    return render_template("admin/ventas/detail.html", venta=venta)


@admin_bp.route("/ventas/<int:venta_id>/cancelar", methods=["POST"])
@admin_required
def ventas_cancelar(venta_id):
    try:
        call_stored_procedure("sp_CancelarVenta", [venta_id])
        flash(f"Venta #{venta_id} cancelada correctamente.", "success")
    except Exception as e:
        flash(f"Error al cancelar la venta: {e}", "danger")

    return redirect(url_for("admin.ventas_list"))
