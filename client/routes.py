from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from utils.database import execute_query, call_stored_procedure

client_bp = Blueprint("client", __name__)


# -------------------------------------------------------------------
# Filtro: sólo clientes logueados
# -------------------------------------------------------------------
@client_bp.before_request
def require_client_login():
    if "user_id" not in session or session.get("es_administrador"):
        return redirect(url_for("auth.login"))


# -------------------------------------------------------------------
# Dashboard de cliente
# -------------------------------------------------------------------
@client_bp.route("/dashboard")
def dashboard():
    cliente_id = session.get("user_id")

    # Vehículos disponibles
    vehiculos = execute_query(
        """
        SELECT
            vehiculo_id,
            marca,
            modelo,
            anio,
            precio,
            color,
            tipo,
            estado_disponibilidad,
            imagen_url
        FROM Vehiculos
        WHERE estado_disponibilidad = 'Disponible'
        ORDER BY marca, modelo
        """
    )

        # Resumen rápido (cuántos disponibles)
    resumen = {
        "vehiculos_disponibles": len(vehiculos),
    }

    # Vehículos “populares” (primeros 3 como demo)
    populares = vehiculos[:3]

    return render_template(
        "client/dashboard.html",
        vehiculos=vehiculos,
        resumen=resumen,
        populares=populares,
    )


# -------------------------------------------------------------------
# Catálogo de vehículos
# -------------------------------------------------------------------
@client_bp.route("/catalogo")
def catalogo():
    vehiculos = execute_query(
        """
        SELECT
            vehiculo_id,
            marca,
            modelo,
            anio,
            precio,
            color,
            tipo,
            estado_disponibilidad,
            descripcion,
            imagen_url
        FROM Vehiculos
        WHERE estado_disponibilidad = 'Disponible'
        ORDER BY fecha_ingreso DESC, vehiculo_id DESC;
        """
    )

    # Para filtros
    marcas = sorted({v["marca"] for v in vehiculos})
    tipos = sorted({v["tipo"] for v in vehiculos})

    return render_template(
        "client/catalogo.html",
        vehiculos=vehiculos,
        marcas=marcas,
        tipos=tipos,
    )


# -------------------------------------------------------------------
# Comprar vehículo
# -------------------------------------------------------------------
@client_bp.route("/comprar/<int:vehiculo_id>", methods=["POST"])
def comprar(vehiculo_id):
    cliente_id = session.get("user_id")
    if not cliente_id:
        return redirect(url_for("auth.login"))

    # Empleado fijo de ejemplo
    empleado_id = 2
    metodo_pago = "Tarjeta"

    try:
        result = call_stored_procedure(
            "sp_RegistrarVenta",
            (cliente_id, empleado_id, vehiculo_id, metodo_pago),
        )

        mensaje_flash = None
        if isinstance(result, list) and result:
            row = result[0]
            if row.get("resultado") == "Éxito":
                mensaje_flash = row.get("mensaje")

        if not mensaje_flash:
            raise RuntimeError("El procedimiento no devolvió un resultado de éxito.")

        flash(mensaje_flash, "success")
    except Exception as e:
        flash(f"Error al registrar la venta: {e}", "danger")

    return redirect(url_for("client.dashboard"))


# -------------------------------------------------------------------
# PERFIL DE CLIENTE  <<< ESTE ES EL ENDPOINT QUE FALTABA
# -------------------------------------------------------------------
@client_bp.route("/perfil")
def perfil():
    cliente_id = session.get("user_id")
    if not cliente_id:
        return redirect(url_for("auth.login"))

    filas = execute_query(
        """
        SELECT
            cliente_id,
            nombre_completo,
            email,
            telefono,
            direccion,
            fecha_registro
        FROM Clientes
        WHERE cliente_id = ?
        """,
        (cliente_id,),
    )

    if not filas:
        flash("No se encontró información del cliente.", "warning")
        return redirect(url_for("client.dashboard"))

    cliente = filas[0]

    return render_template("client/perfil.html", cliente=cliente)
