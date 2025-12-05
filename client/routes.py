from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from utils.database import execute_query, call_stored_procedure

client_bp = Blueprint('client', __name__)


# -------------------------------------------------------------------
# Filtro: sólo clientes logueados
# -------------------------------------------------------------------
@client_bp.before_request
def require_client_login():
    # Si no hay sesión o es admin, mándalo al login
    if 'user_id' not in session or session.get('es_administrador'):
        return redirect(url_for('auth.login'))


# -------------------------------------------------------------------
# Dashboard de cliente
# -------------------------------------------------------------------
@client_bp.route('/dashboard')
def dashboard():
    cliente_id = session.get('user_id')

    # Vehículos (solo disponibles)
    vehiculos = execute_query("""
        SELECT
            vehiculo_id,
            marca,
            modelo,
            anio,
            precio,
            estado_disponibilidad
        FROM Vehiculos
        WHERE estado_disponibilidad = 'Disponible'
        ORDER BY marca, modelo
    """)

    # Historial de compras desde el SP
    historial = []
    try:
        historial = call_stored_procedure('sp_HistorialComprasCliente', (cliente_id,))
    except Exception as e:
        flash(f'Error al cargar historial de compras: {e}', 'danger')

    return render_template(
        'client/dashboard.html',
        vehiculos=vehiculos,
        historial=historial
    )


# -------------------------------------------------------------------
# Comprar vehículo
# -------------------------------------------------------------------
@client_bp.route('/comprar/<int:vehiculo_id>', methods=['POST'])
def comprar(vehiculo_id):
    cliente_id = session.get('user_id')
    # Por ahora usamos un empleado fijo (id 2) para registrar la venta
    empleado_id = 2
    metodo_pago = 'Tarjeta'

    try:
        # Llamar al SP
        result = call_stored_procedure(
            'sp_RegistrarVenta',
            (cliente_id, empleado_id, vehiculo_id, metodo_pago)
        )

        # result debe ser una lista de dicts con columnas: resultado, venta_id, mensaje
        mensaje_flash = None
        if isinstance(result, list) and len(result) > 0:
            row = result[0]
            if row.get('resultado') == 'Éxito':
                mensaje_flash = row.get('mensaje')

        # Si por alguna razón el SP no devolvió nada legible, consideramos que falló
        if not mensaje_flash:
            raise RuntimeError('El procedimiento no devolvió un resultado de éxito.')

        flash(mensaje_flash, 'success')

    except Exception as e:
        flash(f'Error al registrar la venta: {e}', 'danger')

    return redirect(url_for('client.dashboard'))
