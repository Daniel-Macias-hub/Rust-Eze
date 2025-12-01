from flask import Blueprint, render_template, request, jsonify, session
from utils.security import client_required
from utils.database import execute_query

client_bp = Blueprint('client', __name__)

@client_bp.route('/dashboard')
@client_required
def dashboard():
    """Panel de control cliente"""
    cliente_id = session.get('user_id')
    
    try:
        # Obtener historial de compras del cliente
        compras = execute_query("""
            SELECT 
                v.venta_id, v.fecha_venta, v.total_venta, v.metodo_pago, v.estado_venta,
                ve.marca, ve.modelo, ve.anio, ve.color, ve.tipo
            FROM Ventas v
            JOIN Detalle_Ventas dv ON v.venta_id = dv.venta_id
            JOIN Vehiculos ve ON dv.vehiculo_id = ve.vehiculo_id
            WHERE v.cliente_id = ?
            ORDER BY v.fecha_venta DESC
        """, (cliente_id,))
        
        # Obtener vehículos disponibles (solo 4 para el dashboard)
        vehiculos = execute_query("""
            SELECT vehiculo_id, marca, modelo, anio, precio, color, tipo, imagen_url, descripcion
            FROM Vehiculos 
            WHERE estado_disponibilidad = 'Disponible'
            ORDER BY precio DESC
            LIMIT 4
        """)
        
    except Exception as e:
        compras = []
        vehiculos = []
        # En producción usar logger
    
    return render_template('client/dashboard.html', 
                         compras=compras, 
                         vehiculos=vehiculos)

@client_bp.route('/catalogo')
@client_required
def catalogo():
    """Catálogo completo de vehículos"""
    try:
        # Filtros
        marca = request.args.get('marca')
        tipo = request.args.get('tipo')
        precio_min = request.args.get('precio_min')
        precio_max = request.args.get('precio_max')
        
        query = """
            SELECT vehiculo_id, marca, modelo, anio, precio, color, tipo, 
                   imagen_url, descripcion, estado_disponibilidad
            FROM Vehiculos 
            WHERE estado_disponibilidad = 'Disponible'
        """
        
        params = []
        
        if marca and marca != 'todas':
            query += " AND marca = ?"
            params.append(marca)
        
        if tipo and tipo != 'todos':
            query += " AND tipo = ?"
            params.append(tipo)
        
        if precio_min:
            query += " AND precio >= ?"
            params.append(float(precio_min))
        
        if precio_max:
            query += " AND precio <= ?"
            params.append(float(precio_max))
        
        query += " ORDER BY precio DESC"
        
        vehiculos = execute_query(query, params)
        
        # Obtener marcas únicas para filtros
        marcas = execute_query("SELECT DISTINCT marca FROM Vehiculos WHERE estado_disponibilidad = 'Disponible'")
        marcas = [marca['marca'] for marca in marcas]
        
    except Exception as e:
        vehiculos = []
        marcas = []
    
    return render_template('client/catalog.html', 
                         vehiculos=vehiculos, 
                         marcas=marcas)

@client_bp.route('/perfil')
@client_required
def perfil():
    """Perfil del cliente"""
    cliente_id = session.get('user_id')
    
    try:
        cliente_data = execute_query("""
            SELECT cliente_id, nombre_completo, email, telefono, direccion, 
                   tipo_documento, numero_documento, fecha_registro
            FROM Clientes 
            WHERE cliente_id = ?
        """, (cliente_id,))
        
        cliente = cliente_data[0] if cliente_data else None
        
    except Exception as e:
        cliente = None
    
    return render_template('client/profile.html', cliente=cliente)

@client_bp.route('/api/actualizar-perfil', methods=['POST'])
@client_required
def api_actualizar_perfil():
    """API para actualizar perfil del cliente"""
    try:
        data = request.get_json()
        cliente_id = session.get('user_id')
        
        telefono = data.get('telefono')
        direccion = data.get('direccion')
        
        execute_query("""
            UPDATE Clientes 
            SET telefono = ?, direccion = ? 
            WHERE cliente_id = ?
        """, (telefono, direccion, cliente_id))
        
        # Actualizar sesión si es necesario
        session['user_telefono'] = telefono
        
        return jsonify({
            'success': True,
            'message': 'Perfil actualizado exitosamente'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al actualizar perfil: {str(e)}'
        }), 400

@client_bp.route('/api/solicitar-test-drive', methods=['POST'])
@client_required
def api_solicitar_test_drive():
    """API para solicitar test drive"""
    try:
        data = request.get_json()
        vehiculo_id = data.get('vehiculo_id')
        fecha_solicitud = data.get('fecha_solicitud')
        cliente_id = session.get('user_id')
        
        # Aquí implementarías la lógica para programar test drive
        # Por ahora solo es un placeholder
        
        # Obtener información del vehículo para el mensaje
        vehiculo = execute_query("SELECT marca, modelo FROM Vehiculos WHERE vehiculo_id = ?", (vehiculo_id,))
        
        if vehiculo:
            vehiculo_info = f"{vehiculo[0]['marca']} {vehiculo[0]['modelo']}"
            mensaje = f"Solicitud de test drive para {vehiculo_info} el {fecha_solicitud} recibida. Nos contactaremos pronto."
        else:
            mensaje = "Solicitud de test drive recibida. Nos contactaremos pronto."
        
        return jsonify({
            'success': True,
            'message': mensaje
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al solicitar test drive: {str(e)}'
        }), 400

@client_bp.route('/api/contactar-asesor', methods=['POST'])
@client_required
def api_contactar_asesor():
    """API para contactar a un asesor"""
    try:
        data = request.get_json()
        mensaje = data.get('mensaje')
        vehiculo_id = data.get('vehiculo_id')
        cliente_id = session.get('user_id')
        
        # Obtener información del cliente
        cliente = execute_query("SELECT nombre_completo, email FROM Clientes WHERE cliente_id = ?", (cliente_id,))
        
        if cliente:
            nombre_cliente = cliente[0]['nombre_completo']
            
            # Aquí normalmente enviarías un email o notificación al asesor
            # Por ahora solo retornamos un mensaje de éxito
            
            return jsonify({
                'success': True,
                'message': f'Solicitud de contacto enviada. Un asesor se comunicará con {nombre_cliente} pronto.'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Error: Cliente no encontrado'
            }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al contactar asesor: {str(e)}'
        }), 400

@client_bp.route('/historial-compras')
@client_required
def historial_compras():
    """Historial completo de compras"""
    cliente_id = session.get('user_id')
    
    try:
        compras = execute_query("""
            SELECT 
                v.venta_id, v.fecha_venta, v.total_venta, v.metodo_pago, v.estado_venta,
                ve.marca, ve.modelo, ve.anio, ve.color, ve.tipo, ve.descripcion,
                e.nombre_completo as asesor
            FROM Ventas v
            JOIN Detalle_Ventas dv ON v.venta_id = dv.venta_id
            JOIN Vehiculos ve ON dv.vehiculo_id = ve.vehiculo_id
            JOIN Empleados e ON v.empleado_id = e.empleado_id
            WHERE v.cliente_id = ?
            ORDER BY v.fecha_venta DESC
        """, (cliente_id,))
        
    except Exception as e:
        compras = []
    
    return render_template('client/historial_compras.html', compras=compras)