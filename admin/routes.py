from flask import Blueprint, render_template, request, jsonify, session, flash
from utils.security import admin_required
from utils.database import execute_query

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Panel de control administrador"""
    try:
        # Obtener estadísticas
        stats_query = """
            SELECT 
                (SELECT COUNT(*) FROM Vehiculos) as total_vehiculos,
                (SELECT COUNT(*) FROM Vehiculos WHERE estado_disponibilidad = 'Disponible') as vehiculos_disponibles,
                (SELECT COUNT(*) FROM Ventas WHERE strftime('%Y-%m', fecha_venta) = strftime('%Y-%m', 'now')) as ventas_mes,
                (SELECT COUNT(*) FROM Clientes WHERE activo = 1) as total_clientes
        """
        
        stats_result = execute_query(stats_query)
        stats = stats_result[0] if stats_result else {}
        
    except Exception as e:
        flash(f'Error al cargar estadísticas: {str(e)}', 'danger')
        stats = {}
    
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/vehiculos')
@admin_required
def vehiculos():
    """Gestión de vehículos"""
    try:
        vehiculos = execute_query("""
            SELECT vehiculo_id, marca, modelo, anio, precio, color, tipo, 
                   estado_disponibilidad, imagen_url, descripcion
            FROM Vehiculos 
            ORDER BY fecha_ingreso DESC
        """)
    except Exception as e:
        flash(f'Error al cargar vehículos: {str(e)}', 'danger')
        vehiculos = []
    
    return render_template('admin/vehiculos.html', vehiculos=vehiculos)

@admin_bp.route('/ventas')
@admin_required
def ventas():
    """Gestión de ventas"""
    try:
        ventas_data = execute_query("""
            SELECT v.venta_id, c.nombre_completo as cliente, e.nombre_completo as empleado,
                   v.fecha_venta, v.total_venta, v.metodo_pago, v.estado_venta
            FROM Ventas v
            JOIN Clientes c ON v.cliente_id = c.cliente_id
            JOIN Empleados e ON v.empleado_id = e.empleado_id
            ORDER BY v.fecha_venta DESC
        """)
    except Exception as e:
        flash(f'Error al cargar ventas: {str(e)}', 'danger')
        ventas_data = []
    
    return render_template('admin/sales.html', ventas=ventas_data)

@admin_bp.route('/clientes')
@admin_required
def clientes():
    """Gestión de clientes"""
    try:
        clientes_data = execute_query("""
            SELECT cliente_id, nombre_completo, email, telefono, direccion, 
                   tipo_documento, numero_documento, fecha_registro
            FROM Clientes 
            WHERE activo = 1
            ORDER BY fecha_registro DESC
        """)
    except Exception as e:
        flash(f'Error al cargar clientes: {str(e)}', 'danger')
        clientes_data = []
    
    return render_template('admin/clientes.html', clientes=clientes_data)

@admin_bp.route('/api/registrar-venta', methods=['POST'])
@admin_required
def api_registrar_venta():
    """API para registrar venta"""
    try:
        data = request.get_json()
        cliente_id = data.get('cliente_id')
        empleado_id = session.get('user_id')
        vehiculo_id = data.get('vehiculo_id')
        metodo_pago = data.get('metodo_pago')
        
        # Obtener precio del vehículo
        vehiculo = execute_query("SELECT precio FROM Vehiculos WHERE vehiculo_id = ?", (vehiculo_id,))
        if not vehiculo:
            return jsonify({'success': False, 'message': 'Vehículo no encontrado'}), 400
        
        precio = vehiculo[0]['precio']
        
        # Insertar venta
        venta_query = """
            INSERT INTO Ventas (cliente_id, empleado_id, total_venta, metodo_pago)
            VALUES (?, ?, ?, ?)
        """
        execute_query(venta_query, (cliente_id, empleado_id, precio, metodo_pago))
        
        # Obtener ID de la venta recién insertada
        venta_id = execute_query("SELECT last_insert_rowid() as id")[0]['id']
        
        # Insertar detalle
        detalle_query = """
            INSERT INTO Detalle_Ventas (venta_id, vehiculo_id, precio_unitario)
            VALUES (?, ?, ?)
        """
        execute_query(detalle_query, (venta_id, vehiculo_id, precio))
        
        # Actualizar estado del vehículo
        execute_query(
            "UPDATE Vehiculos SET estado_disponibilidad = 'Vendido' WHERE vehiculo_id = ?", 
            (vehiculo_id,)
        )
        
        return jsonify({
            'success': True,
            'message': 'Venta registrada exitosamente',
            'venta_id': venta_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al registrar venta: {str(e)}'
        }), 400

@admin_bp.route('/api/cancelar-venta', methods=['POST'])
@admin_required
def api_cancelar_venta():
    """API para cancelar venta"""
    try:
        data = request.get_json()
        venta_id = data.get('venta_id')
        
        # Verificar que la venta existe y está activa
        venta = execute_query("SELECT estado_venta FROM Ventas WHERE venta_id = ?", (venta_id,))
        if not venta:
            return jsonify({'success': False, 'message': 'Venta no encontrada'}), 400
        
        if venta[0]['estado_venta'] != 'Activa':
            return jsonify({'success': False, 'message': 'Solo se pueden cancelar ventas activas'}), 400
        
        # Cancelar venta
        execute_query("UPDATE Ventas SET estado_venta = 'Cancelada' WHERE venta_id = ?", (venta_id,))
        
        # Liberar vehículos
        vehiculos_query = """
            SELECT dv.vehiculo_id 
            FROM Detalle_Ventas dv 
            WHERE dv.venta_id = ?
        """
        vehiculos = execute_query(vehiculos_query, (venta_id,))
        
        for vehiculo in vehiculos:
            execute_query(
                "UPDATE Vehiculos SET estado_disponibilidad = 'Disponible' WHERE vehiculo_id = ?", 
                (vehiculo['vehiculo_id'],)
            )
        
        return jsonify({
            'success': True,
            'message': 'Venta cancelada exitosamente'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al cancelar venta: {str(e)}'
        }), 400

@admin_bp.route('/api/agregar-vehiculo', methods=['POST'])
@admin_required
def api_agregar_vehiculo():
    """API para agregar nuevo vehículo"""
    try:
        data = request.get_json()
        marca = data.get('marca')
        modelo = data.get('modelo')
        anio = data.get('anio')
        precio = data.get('precio')
        color = data.get('color')
        tipo = data.get('tipo')
        descripcion = data.get('descripcion', '')
        
        query = """
            INSERT INTO Vehiculos (marca, modelo, anio, precio, color, tipo, descripcion)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        execute_query(query, (marca, modelo, anio, precio, color, tipo, descripcion))
        
        return jsonify({
            'success': True,
            'message': 'Vehículo agregado exitosamente'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al agregar vehículo: {str(e)}'
        }), 400

@admin_bp.route('/reportes')
@admin_required
def reportes():
    """Página de reportes"""
    try:
        # Reporte de ventas por mes
        ventas_mes = execute_query("""
            SELECT 
                strftime('%Y-%m', fecha_venta) as mes,
                COUNT(*) as total_ventas,
                SUM(total_venta) as ingreso_total
            FROM Ventas 
            WHERE estado_venta = 'Activa'
            GROUP BY strftime('%Y-%m', fecha_venta)
            ORDER BY mes DESC
            LIMIT 6
        """)
        
        # Marcas más vendidas
        marcas_vendidas = execute_query("""
            SELECT 
                v.marca,
                COUNT(*) as unidades_vendidas,
                SUM(ve.total_venta) as ingreso_total
            FROM Ventas ve
            JOIN Detalle_Ventas dv ON ve.venta_id = dv.venta_id
            JOIN Vehiculos v ON dv.vehiculo_id = v.vehiculo_id
            WHERE ve.estado_venta = 'Activa'
            GROUP BY v.marca
            ORDER BY unidades_vendidas DESC
        """)
        
    except Exception as e:
        ventas_mes = []
        marcas_vendidas = []
        flash(f'Error al cargar reportes: {str(e)}', 'danger')
    
    return render_template('admin/reports.html', 
                         ventas_mes=ventas_mes, 
                         marcas_vendidas=marcas_vendidas)