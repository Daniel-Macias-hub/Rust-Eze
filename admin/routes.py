"""
Rutas del panel de administración - Rust-Eze Agency
Conectado a SQL Server 2022 Express con procedimientos almacenados
"""

from flask import Blueprint, render_template, request, jsonify, session, flash
from utils.security import admin_required
from utils.database_sqlserver import execute_query, call_stored_procedure
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

# ===================================================================
# RUTAS PRINCIPALES
# ===================================================================

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Panel de control administrador con estadísticas reales"""
    try:
        # Obtener estadísticas REALES desde SQL Server
        stats_query = """
        SELECT 
            (SELECT COUNT(*) FROM Vehiculos) as total_vehiculos,
            (SELECT COUNT(*) FROM Vehiculos WHERE estado_disponibilidad = 'Disponible') as vehiculos_disponibles,
            (SELECT COUNT(*) FROM Ventas 
             WHERE estado_venta = 'Activa' 
             AND MONTH(fecha_venta) = MONTH(GETDATE())
             AND YEAR(fecha_venta) = YEAR(GETDATE())) as ventas_mes,
            (SELECT COUNT(*) FROM Clientes WHERE activo = 1) as total_clientes,
            (SELECT COUNT(*) FROM Clientes 
             WHERE activo = 1 
             AND MONTH(fecha_registro) = MONTH(GETDATE())
             AND YEAR(fecha_registro) = YEAR(GETDATE())) as clientes_nuevos,
            (SELECT ISNULL(SUM(total_venta), 0) FROM Ventas 
             WHERE estado_venta = 'Activa' 
             AND MONTH(fecha_venta) = MONTH(GETDATE())
             AND YEAR(fecha_venta) = YEAR(GETDATE())) as ingresos_mes
        """
        
        stats_result = execute_query(stats_query)
        stats = stats_result[0] if stats_result else {}
        
        # Calcular tasa de conversión (ejemplo)
        if stats.get('total_clientes', 0) > 0:
            stats['tasa_conversion'] = round(
                (stats.get('ventas_mes', 0) / stats.get('total_clientes', 1)) * 100, 
                1
            )
        else:
            stats['tasa_conversion'] = 0
            
    except Exception as e:
        logger.error(f'Error al cargar estadísticas: {str(e)}')
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
                   estado_disponibilidad, imagen_url, descripcion,
                   FORMAT(fecha_ingreso, 'yyyy-MM-dd') as fecha_ingreso
            FROM Vehiculos 
            ORDER BY fecha_ingreso DESC
        """)
    except Exception as e:
        logger.error(f'Error al cargar vehículos: {str(e)}')
        flash(f'Error al cargar vehículos: {str(e)}', 'danger')
        vehiculos = []
    
    return render_template('admin/vehiculos.html', vehiculos=vehiculos)

@admin_bp.route('/ventas')
@admin_required
def ventas():
    """Gestión de ventas"""
    try:
        ventas_data = execute_query("""
            SELECT 
                v.venta_id, 
                c.nombre_completo as cliente, 
                e.nombre_completo as empleado,
                FORMAT(v.fecha_venta, 'yyyy-MM-dd HH:mm') as fecha_venta, 
                v.total_venta, 
                v.metodo_pago, 
                v.estado_venta
            FROM Ventas v
            JOIN Clientes c ON v.cliente_id = c.cliente_id
            JOIN Empleados e ON v.empleado_id = e.empleado_id
            ORDER BY v.fecha_venta DESC
        """)
    except Exception as e:
        logger.error(f'Error al cargar ventas: {str(e)}')
        flash(f'Error al cargar ventas: {str(e)}', 'danger')
        ventas_data = []
    
    return render_template('admin/sales.html', ventas=ventas_data)

@admin_bp.route('/clientes')
@admin_required
def clientes():
    """Gestión de clientes"""
    try:
        clientes_data = execute_query("""
            SELECT 
                cliente_id, 
                nombre_completo, 
                email, 
                telefono, 
                direccion, 
                tipo_documento, 
                numero_documento,
                FORMAT(fecha_registro, 'yyyy-MM-dd') as fecha_registro
            FROM Clientes 
            WHERE activo = 1
            ORDER BY fecha_registro DESC
        """)
    except Exception as e:
        logger.error(f'Error al cargar clientes: {str(e)}')
        flash(f'Error al cargar clientes: {str(e)}', 'danger')
        clientes_data = []
    
    return render_template('admin/clientes.html', clientes=clientes_data)

@admin_bp.route('/reportes')
@admin_required
def reportes():
    """Página de reportes avanzados"""
    try:
        # Reporte de ventas por mes (para gráfico)
        ventas_mes = execute_query("""
            SELECT 
                FORMAT(fecha_venta, 'yyyy-MM') as mes,
                COUNT(*) as total_ventas,
                SUM(total_venta) as ingreso_total
            FROM Ventas 
            WHERE estado_venta = 'Activa'
            AND fecha_venta >= DATEADD(MONTH, -6, GETDATE())
            GROUP BY FORMAT(fecha_venta, 'yyyy-MM')
            ORDER BY mes DESC
        """)
        
        # Marcas más vendidas
        marcas_vendidas = execute_query("""
            SELECT TOP 10
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
        logger.error(f'Error al cargar reportes: {str(e)}')
        flash(f'Error al cargar reportes: {str(e)}', 'danger')
        ventas_mes = []
        marcas_vendidas = []
    
    return render_template('admin/reports.html', 
                         ventas_mes=ventas_mes, 
                         marcas_vendidas=marcas_vendidas)

# ===================================================================
# API ENDPOINTS - CONSULTAS AVANZADAS (REQUISITO 6)
# ===================================================================

@admin_bp.route('/api/ventas-por-mes-marca')
@admin_required
def api_ventas_por_mes_marca():
    """
    REQUISITO 6.1: PIVOT - Ventas por mes y marca
    Devuelve datos para gráficos
    """
    try:
        # Consulta simplificada para desarrollo
        # En producción usarías PIVOT dinámico
        pivot_query = """
        SELECT 
            v.marca,
            FORMAT(ve.fecha_venta, 'yyyy-MM') as mes,
            COUNT(*) as total_ventas,
            SUM(ve.total_venta) as ingreso_total
        FROM Ventas ve
        JOIN Detalle_Ventas dv ON ve.venta_id = dv.venta_id
        JOIN Vehiculos v ON dv.vehiculo_id = v.vehiculo_id
        WHERE ve.estado_venta = 'Activa'
        AND ve.fecha_venta >= DATEADD(MONTH, -6, GETDATE())
        GROUP BY v.marca, FORMAT(ve.fecha_venta, 'yyyy-MM')
        ORDER BY mes DESC, total_ventas DESC
        """
        
        results = execute_query(pivot_query)
        
        # Transformar para Chart.js
        marcas = sorted(set(r['marca'] for r in results))
        meses = sorted(set(r['mes'] for r in results), reverse=True)
        
        data = {
            'marcas': marcas,
            'meses': meses,
            'datasets': []
        }
        
        for marca in marcas[:5]:  # Top 5 marcas
            marca_data = {
                'label': marca,
                'data': []
            }
            for mes in meses:
                venta = next((r for r in results if r['marca'] == marca and r['mes'] == mes), None)
                marca_data['data'].append(venta['total_ventas'] if venta else 0)
            data['datasets'].append(marca_data)
        
        return jsonify({'success': True, 'data': data})
        
    except Exception as e:
        logger.error(f'Error en PIVOT query: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 400

@admin_bp.route('/api/clientes-clasificacion')
@admin_required
def api_clientes_clasificacion():
    """
    REQUISITO 6.2: CASE - Clasificación de clientes por nivel de compra
    """
    try:
        case_query = """
        SELECT 
            c.cliente_id,
            c.nombre_completo,
            c.email,
            COUNT(v.venta_id) as total_compras,
            COALESCE(SUM(v.total_venta), 0) as monto_total,
            -- REQUISITO: Instrucción CASE
            CASE 
                WHEN COUNT(v.venta_id) = 0 THEN 'Sin Compras'
                WHEN COALESCE(SUM(v.total_venta), 0) < 500000 THEN 'Básico'
                WHEN COALESCE(SUM(v.total_venta), 0) < 1500000 THEN 'Frecuente'
                ELSE 'Premium'
            END as categoria_cliente,
            CASE 
                WHEN COUNT(v.venta_id) = 0 THEN 'gray'
                WHEN COALESCE(SUM(v.total_venta), 0) < 500000 THEN 'blue'
                WHEN COALESCE(SUM(v.total_venta), 0) < 1500000 THEN 'green'
                ELSE 'gold'
            END as color_categoria
        FROM Clientes c
        LEFT JOIN Ventas v ON c.cliente_id = v.cliente_id AND v.estado_venta = 'Activa'
        GROUP BY c.cliente_id, c.nombre_completo, c.email
        ORDER BY monto_total DESC;
        """
        
        results = execute_query(case_query)
        return jsonify({'success': True, 'data': results})
        
    except Exception as e:
        logger.error(f'Error en CASE query: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 400

@admin_bp.route('/api/ranking-marcas')
@admin_required
def api_ranking_marcas():
    """
    REQUISITO 6.3: RANKING - Top marcas más vendidas
    """
    try:
        ranking_query = """
        WITH VentasMarca AS (
            SELECT 
                v.marca,
                COUNT(*) as unidades_vendidas,
                SUM(ve.total_venta) as ingreso_total,
                -- REQUISITO: Funciones de ventana
                ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) as row_num,
                RANK() OVER (ORDER BY COUNT(*) DESC) as rank,
                DENSE_RANK() OVER (ORDER BY COUNT(*) DESC) as dense_rank
            FROM Ventas ve
            JOIN Detalle_Ventas dv ON ve.venta_id = dv.venta_id
            JOIN Vehiculos v ON dv.vehiculo_id = v.vehiculo_id
            WHERE ve.estado_venta = 'Activa'
            AND ve.fecha_venta >= DATEADD(year, -1, GETDATE())
            GROUP BY v.marca
        )
        SELECT 
            marca,
            unidades_vendidas,
            ingreso_total,
            row_num,
            rank,
            dense_rank
        FROM VentasMarca
        ORDER BY rank
        OFFSET 0 ROWS FETCH NEXT 10 ROWS ONLY;
        """
        
        results = execute_query(ranking_query)
        return jsonify({'success': True, 'data': results})
        
    except Exception as e:
        logger.error(f'Error en RANKING query: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 400

# ===================================================================
# API ENDPOINTS - PROCEDIMIENTOS ALMACENADOS (REQUISITO 3)
# ===================================================================

@admin_bp.route('/api/registrar-venta-sp', methods=['POST'])
@admin_required
def api_registrar_venta_sp():
    """
    REQUISITO 3.1: Registrar venta usando procedimiento almacenado
    REQUISITO 8: TRY/CATCH completo
    """
    try:
        data = request.get_json()
        cliente_id = data.get('cliente_id')
        empleado_id = session.get('user_id')
        vehiculo_id = data.get('vehiculo_id')
        metodo_pago = data.get('metodo_pago')
        
        # Validaciones
        if not all([cliente_id, empleado_id, vehiculo_id, metodo_pago]):
            return jsonify({
                'success': False,
                'message': 'Todos los campos son requeridos'
            }), 400
        
        # REQUISITO: Llamar procedimiento almacenado
        logger.info(f"Ejecutando sp_RegistrarVenta: cliente={cliente_id}, empleado={empleado_id}, vehiculo={vehiculo_id}")
        
        result = call_stored_procedure(
            'sp_RegistrarVenta',
            [cliente_id, empleado_id, vehiculo_id, metodo_pago]
        )
        
        if result and len(result) > 0:
            return jsonify({
                'success': True,
                'message': result[0].get('mensaje', 'Venta registrada exitosamente'),
                'venta_id': result[0].get('venta_id')
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Venta registrada exitosamente'
            })
            
    except Exception as e:
        logger.error(f'Error en sp_RegistrarVenta: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error al registrar venta: {str(e)}'
        }), 400

@admin_bp.route('/api/cancelar-venta-sp', methods=['POST'])
@admin_required
def api_cancelar_venta_sp():
    """
    REQUISITO 3.2: Cancelar venta usando procedimiento almacenado
    """
    try:
        data = request.get_json()
        venta_id = data.get('venta_id')
        
        if not venta_id:
            return jsonify({
                'success': False,
                'message': 'ID de venta requerido'
            }), 400
        
        logger.info(f"Ejecutando sp_CancelarVenta: venta_id={venta_id}")
        
        result = call_stored_procedure('sp_CancelarVenta', [venta_id])
        
        if result and len(result) > 0:
            return jsonify({
                'success': True,
                'message': result[0].get('mensaje', 'Venta cancelada exitosamente')
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Venta cancelada exitosamente'
            })
            
    except Exception as e:
        logger.error(f'Error en sp_CancelarVenta: {str(e)}')
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
        estado_disponibilidad = data.get('estado_disponibilidad', 'Disponible')
        descripcion = data.get('descripcion', '')
        imagen_url = data.get('imagen_url', '')
        
        # Validaciones
        required_fields = ['marca', 'modelo', 'anio', 'precio', 'color', 'tipo']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'El campo {field} es requerido'
                }), 400
        
        query = """
            INSERT INTO Vehiculos 
            (marca, modelo, anio, precio, color, tipo, estado_disponibilidad, descripcion, imagen_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        execute_query(query, (marca, modelo, anio, precio, color, tipo, estado_disponibilidad, descripcion, imagen_url))
        
        return jsonify({
            'success': True,
            'message': 'Vehículo agregado exitosamente'
        })
        
    except Exception as e:
        logger.error(f'Error al agregar vehículo: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error al agregar vehículo: {str(e)}'
        }), 400

@admin_bp.route('/api/registrar-venta', methods=['POST'])
@admin_required
def api_registrar_venta():
    """API alternativa para registrar venta (sin procedimiento)"""
    try:
        data = request.get_json()
        cliente_id = data.get('cliente_id')
        empleado_id = session.get('user_id')
        vehiculo_id = data.get('vehiculo_id')
        metodo_pago = data.get('metodo_pago')
        
        # Validaciones
        if not all([cliente_id, empleado_id, vehiculo_id, metodo_pago]):
            return jsonify({'success': False, 'message': 'Todos los campos son requeridos'}), 400
        
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
        venta_id = execute_query("SELECT SCOPE_IDENTITY() as id")[0]['id']
        
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
        logger.error(f'Error al registrar venta: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error al registrar venta: {str(e)}'
        }), 400

@admin_bp.route('/api/cancelar-venta', methods=['POST'])
@admin_required
def api_cancelar_venta():
    """API alternativa para cancelar venta (sin procedimiento)"""
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
        logger.error(f'Error al cancelar venta: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error al cancelar venta: {str(e)}'
        }), 400

# ===================================================================
# API ENDPOINTS - REPORTES Y CONSULTAS (REQUISITO 3.3-3.5)
# ===================================================================

@admin_bp.route('/api/historial-cliente/<int:cliente_id>')
@admin_required
def api_historial_cliente(cliente_id):
    """
    REQUISITO 3.2: Historial de compras de cliente
    """
    try:
        historial_query = """
        SELECT 
            v.venta_id,
            FORMAT(v.fecha_venta, 'yyyy-MM-dd HH:mm') as fecha_venta,
            v.total_venta,
            v.metodo_pago,
            v.estado_venta,
            ve.marca,
            ve.modelo,
            ve.anio,
            ve.color,
            ve.tipo,
            e.nombre_completo as vendedor
        FROM Ventas v
        JOIN Detalle_Ventas dv ON v.venta_id = dv.venta_id
        JOIN Vehiculos ve ON dv.vehiculo_id = ve.vehiculo_id
        JOIN Empleados e ON v.empleado_id = e.empleado_id
        WHERE v.cliente_id = ?
        ORDER BY v.fecha_venta DESC;
        """
        
        results = execute_query(historial_query, [cliente_id])
        return jsonify({'success': True, 'data': results})
        
    except Exception as e:
        logger.error(f'Error al obtener historial cliente: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 400

@admin_bp.route('/api/disponibilidad-vehiculos')
@admin_required
def api_disponibilidad_vehiculos():
    """
    REQUISITO 3.4: Disponibilidad de vehículos por marca y tipo
    """
    try:
        marca = request.args.get('marca')
        tipo = request.args.get('tipo')
        
        query = """
        SELECT 
            marca,
            tipo,
            estado_disponibilidad,
            COUNT(*) as cantidad,
            MIN(precio) as precio_min,
            MAX(precio) as precio_max,
            AVG(precio) as precio_promedio
        FROM Vehiculos
        WHERE 1=1
        """
        
        params = []
        if marca and marca != 'todas':
            query += " AND marca = ?"
            params.append(marca)
        if tipo and tipo != 'todos':
            query += " AND tipo = ?"
            params.append(tipo)
            
        query += " GROUP BY marca, tipo, estado_disponibilidad ORDER BY marca, tipo;"
        
        results = execute_query(query, params)
        return jsonify({'success': True, 'data': results})
        
    except Exception as e:
        logger.error(f'Error al obtener disponibilidad: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 400

@admin_bp.route('/api/marcas-modelos-vendidos')
@admin_required
def api_marcas_modelos_vendidos():
    """
    REQUISITO 3.3: Marcas y modelos más vendidos
    """
    try:
        top = request.args.get('top', 10, type=int)
        
        query = """
        SELECT TOP (?) 
            v.marca,
            v.modelo,
            COUNT(*) as unidades_vendidas,
            SUM(ve.total_venta) as ingreso_total,
            ROUND(AVG(v.precio), 2) as precio_promedio
        FROM Ventas ve
        JOIN Detalle_Ventas dv ON ve.venta_id = dv.venta_id
        JOIN Vehiculos v ON dv.vehiculo_id = v.vehiculo_id
        WHERE ve.estado_venta = 'Activa'
        GROUP BY v.marca, v.modelo
        ORDER BY unidades_vendidas DESC, ingreso_total DESC;
        """
        
        results = execute_query(query, [top])
        return jsonify({'success': True, 'data': results})
        
    except Exception as e:
        logger.error(f'Error al obtener marcas/modelos vendidos: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 400

# ===================================================================
# PÁGINA DE AUDITORÍA (REQUISITO 4)
# ===================================================================

@admin_bp.route('/auditoria')
@admin_required
def auditoria():
    """
    REQUISITO 4: Página de auditoría del sistema
    """
    try:
        # Auditoría de ventas
        auditoria_ventas = execute_query("""
            SELECT TOP 50 
                audit_id,
                accion,
                venta_id,
                usuario,
                FORMAT(fecha_evento, 'yyyy-MM-dd HH:mm:ss') as fecha_evento,
                datos_anteriores,
                datos_nuevos
            FROM Auditoria_Ventas 
            ORDER BY fecha_evento DESC
        """)
        
        # Auditoría de vehículos
        auditoria_vehiculos = execute_query("""
            SELECT TOP 50 
                audit_id,
                accion,
                vehiculo_id,
                usuario,
                FORMAT(fecha_evento, 'yyyy-MM-dd HH:mm:ss') as fecha_evento,
                datos_anteriores,
                datos_nuevos
            FROM Auditoria_Vehiculos 
            ORDER BY fecha_evento DESC
        """)
        
        # Errores del sistema
        errores_sistema = execute_query("""
            SELECT TOP 50 
                error_id,
                procedimiento,
                mensaje_error,
                numero_error,
                usuario,
                FORMAT(fecha_error, 'yyyy-MM-dd HH:mm:ss') as fecha_error
            FROM Auditoria_Errores 
            ORDER BY fecha_error DESC
        """)
        
        # Estadísticas de auditoría
        stats_auditoria = execute_query("""
            SELECT 
                (SELECT COUNT(*) FROM Auditoria_Ventas) as total_ventas,
                (SELECT COUNT(*) FROM Auditoria_Vehiculos) as total_vehiculos,
                (SELECT COUNT(*) FROM Auditoria_Errores) as total_errores,
                (SELECT COUNT(*) FROM Auditoria_Ventas WHERE accion = 'INSERT') as inserciones_ventas,
                (SELECT COUNT(*) FROM Auditoria_Ventas WHERE accion = 'UPDATE') as actualizaciones_ventas,
                (SELECT COUNT(*) FROM Auditoria_Ventas WHERE accion = 'DELETE') as eliminaciones_ventas
        """)
        
        stats = stats_auditoria[0] if stats_auditoria else {}
        
    except Exception as e:
        logger.error(f'Error al cargar auditoría: {str(e)}')
        flash(f'Error al cargar auditoría: {str(e)}', 'danger')
        auditoria_ventas = []
        auditoria_vehiculos = []
        errores_sistema = []
        stats = {}
    
    return render_template('admin/auditoria.html',
                         auditoria_ventas=auditoria_ventas,
                         auditoria_vehiculos=auditoria_vehiculos,
                         errores_sistema=errores_sistema,
                         stats=stats)

@admin_bp.route('/api/limpiar-auditoria', methods=['POST'])
@admin_required
def api_limpiar_auditoria():
    """
    Limpiar registros antiguos de auditoría (solo admin)
    """
    try:
        data = request.get_json()
        dias = data.get('dias', 90)  # Por defecto 90 días
        
        # Verificar que días sea válido
        if not isinstance(dias, int) or dias < 1:
            return jsonify({
                'success': False,
                'message': 'Número de días inválido'
            }), 400
        
        # Limpiar auditoría de ventas
        ventas_eliminadas = execute_query("""
            DELETE FROM Auditoria_Ventas 
            WHERE fecha_evento < DATEADD(day, -?, GETDATE())
        """, [dias])
        
        # Limpiar auditoría de vehículos
        vehiculos_eliminadas = execute_query("""
            DELETE FROM Auditoria_Vehiculos 
            WHERE fecha_evento < DATEADD(day, -?, GETDATE())
        """, [dias])
        
        # Limpiar errores (mantener más tiempo para debugging)
        errores_eliminados = execute_query("""
            DELETE FROM Auditoria_Errores 
            WHERE fecha_error < DATEADD(day, -?, GETDATE())
        """, [dias * 2])  # Mantener errores el doble de tiempo
        
        total_eliminados = (
            (ventas_eliminadas.get('rows_affected', 0) if isinstance(ventas_eliminadas, dict) else 0) +
            (vehiculos_eliminadas.get('rows_affected', 0) if isinstance(vehiculos_eliminadas, dict) else 0) +
            (errores_eliminados.get('rows_affected', 0) if isinstance(errores_eliminados, dict) else 0)
        )
        
        return jsonify({
            'success': True,
            'message': f'Auditoría limpiada exitosamente',
            'detalle': {
                'registros_eliminados': total_eliminados,
                'dias': dias,
                'ventas_eliminadas': ventas_eliminadas.get('rows_affected', 0) if isinstance(ventas_eliminadas, dict) else 0,
                'vehiculos_eliminados': vehiculos_eliminadas.get('rows_affected', 0) if isinstance(vehiculos_eliminadas, dict) else 0,
                'errores_eliminados': errores_eliminados.get('rows_affected', 0) if isinstance(errores_eliminados, dict) else 0
            }
        })
        
    except Exception as e:
        logger.error(f'Error al limpiar auditoría: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error al limpiar auditoría: {str(e)}'
        }), 400

# ===================================================================
# FUNCIONES DE UTILIDAD
# ===================================================================

@admin_bp.route('/api/estadisticas-generales')
@admin_required
def api_estadisticas_generales():
    """API para obtener estadísticas generales del sistema"""
    try:
        estadisticas_query = """
        SELECT 
            -- Ventas
            (SELECT COUNT(*) FROM Ventas WHERE estado_venta = 'Activa') as ventas_activas,
            (SELECT COUNT(*) FROM Ventas WHERE estado_venta = 'Cancelada') as ventas_canceladas,
            (SELECT ISNULL(SUM(total_venta), 0) FROM Ventas WHERE estado_venta = 'Activa') as ingreso_total,
            
            -- Vehículos
            (SELECT COUNT(*) FROM Vehiculos WHERE estado_disponibilidad = 'Disponible') as vehiculos_disponibles,
            (SELECT COUNT(*) FROM Vehiculos WHERE estado_disponibilidad = 'Vendido') as vehiculos_vendidos,
            (SELECT COUNT(*) FROM Vehiculos WHERE estado_disponibilidad = 'Reservado') as vehiculos_reservados,
            
            -- Clientes
            (SELECT COUNT(*) FROM Clientes WHERE activo = 1) as clientes_activos,
            (SELECT COUNT(DISTINCT cliente_id) FROM Ventas WHERE estado_venta = 'Activa') as clientes_con_compras,
            
            -- Métodos de pago
            (SELECT COUNT(*) FROM Ventas WHERE metodo_pago = 'Efectivo' AND estado_venta = 'Activa') as pagos_efectivo,
            (SELECT COUNT(*) FROM Ventas WHERE metodo_pago = 'Tarjeta' AND estado_venta = 'Activa') as pagos_tarjeta,
            (SELECT COUNT(*) FROM Ventas WHERE metodo_pago = 'Transferencia' AND estado_venta = 'Activa') as pagos_transferencia
        """
        
        results = execute_query(estadisticas_query)
        return jsonify({'success': True, 'data': results[0] if results else {}})
        
    except Exception as e:
        logger.error(f'Error al obtener estadísticas: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 400

@admin_bp.route('/api/vehiculos-disponibles')
@admin_required
def api_vehiculos_disponibles():
    """API para obtener vehículos disponibles"""
    try:
        query = """
        SELECT 
            vehiculo_id,
            marca,
            modelo,
            anio,
            precio,
            color,
            tipo,
            descripcion
        FROM Vehiculos 
        WHERE estado_disponibilidad = 'Disponible'
        ORDER BY precio DESC
        """
        
        results = execute_query(query)
        return jsonify({'success': True, 'data': results})
        
    except Exception as e:
        logger.error(f'Error al obtener vehículos disponibles: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 400