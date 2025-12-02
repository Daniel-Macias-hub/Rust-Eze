"""
Conexión unificada a SQL Server 2022 Express - VERSIÓN CORREGIDA
Elimina todas las referencias a SQLite
"""

import pyodbc
from flask import g, current_app
import logging
from contextlib import contextmanager
import hashlib

logger = logging.getLogger(__name__)

class SQLServerConnection:
    """Manejador de conexión unificado a SQL Server Express"""
    
    @staticmethod
    def get_connection():
        """Obtener conexión desde el contexto de Flask"""
        if 'sqlserver_conn' not in g:
            try:
                # Usar conexión a SQLEXPRESS (instancia local)
                connection_string = (
                    'DRIVER={ODBC Driver 17 for SQL Server};'
                    'SERVER=localhost\\SQLEXPRESS;'
                    'DATABASE=RustEze_Agency;'
                    'Trusted_Connection=yes;'
                )
                
                g.sqlserver_conn = pyodbc.connect(connection_string)
                g.sqlserver_conn.autocommit = False
                logger.info("✅ Conexión SQL Server Express establecida")
                
            except pyodbc.Error as e:
                logger.error(f"❌ Error conexión SQL Server: {e}")
                # Fallback para desarrollo
                raise ConnectionError(f"No se pudo conectar a SQL Server: {e}")
                
        return g.sqlserver_conn
    
    @staticmethod
    def close_connection(e=None):
        """Cerrar conexión al final del contexto"""
        conn = g.pop('sqlserver_conn', None)
        if conn is not None:
            try:
                conn.close()
                logger.debug("🔌 Conexión SQL Server cerrada")
            except:
                pass

@contextmanager
def get_cursor():
    """Context manager para manejo automático de cursor"""
    conn = SQLServerConnection.get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()

def execute_query(query, params=None, fetch=True):
    """
    Ejecutar consulta SQL con manejo de errores
    """
    try:
        with get_cursor() as cursor:
            if params:
                # Manejar listas de parámetros para IN clauses
                if isinstance(params, (list, tuple)) and '?' in query:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch and query.strip().upper().startswith('SELECT'):
                columns = [column[0] for column in cursor.description] if cursor.description else []
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                return results
            else:
                cursor.connection.commit()
                return {"success": True, "rows_affected": cursor.rowcount}
                
    except pyodbc.Error as e:
        logger.error(f"Error en execute_query: {e}")
        if 'cursor' in locals() and cursor.connection:
            try:
                cursor.connection.rollback()
            except:
                pass
        
        # Registrar error en auditoría
        try:
            error_query = """
            INSERT INTO Auditoria_Errores (procedimiento, mensaje_error, numero_error, usuario)
            VALUES (?, ?, ?, ?)
            """
            with get_cursor() as error_cursor:
                error_cursor.execute(error_query, ('execute_query', str(e), 0, 'SYSTEM'))
                error_cursor.connection.commit()
        except:
            pass
            
        raise e

def call_stored_procedure(proc_name, params=None):
    """
    Ejecutar procedimiento almacenado con parámetros
    """
    try:
        with get_cursor() as cursor:
            if params:
                placeholders = ', '.join(['?'] * len(params))
                exec_stmt = f"{{CALL {proc_name} ({placeholders})}}"
                cursor.execute(exec_stmt, params)
            else:
                cursor.execute(f"{{CALL {proc_name}}}")
            
            # Para SP que retornan resultados
            if cursor.description:
                columns = [column[0] for column in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                return results
            else:
                cursor.connection.commit()
                return {"success": True, "rows_affected": cursor.rowcount}
                
    except pyodbc.Error as e:
        logger.error(f"Error en {proc_name}: {e}")
        
        # Registrar error en auditoría
        try:
            error_query = """
            INSERT INTO Auditoria_Errores (procedimiento, mensaje_error, numero_error, usuario)
            VALUES (?, ?, ?, ?)
            """
            with get_cursor() as error_cursor:
                error_cursor.execute(error_query, (proc_name, str(e), 0, 'SYSTEM'))
                error_cursor.connection.commit()
        except:
            pass
            
        raise e

def init_app(app):
    """Inicializar extensión con Flask app"""
    app.teardown_appcontext(SQLServerConnection.close_connection)
    
    # Verificar conexión al inicio
    with app.app_context():
        try:
            test = execute_query("SELECT @@VERSION as version")
            logger.info(f"✅ SQL Server inicializado: {test[0]['version'][:50]}...")
            
        except Exception as e:
            logger.error(f"❌ Error inicialización SQL Server: {e}")
            logger.warning("⚠️  Asegúrate de que:")
            logger.warning("   1. SQL Server 2022 Express esté instalado")
            logger.warning("   2. La base de datos 'RustEze_Agency' exista")
            logger.warning("   3. El servicio SQL Server esté ejecutándose")
            raise

class User:
    """Clase para manejar usuarios con SQL Server"""
    
    @staticmethod
    def hash_password(password):
        """Hash simple para desarrollo (en producción usar bcrypt)"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def authenticate(email, password, is_admin=False):
        """Autenticar usuario contra SQL Server"""
        try:
            hashed_password = User.hash_password(password)
            
            if is_admin:
                query = """
                    SELECT empleado_id as id, nombre_completo, email, puesto, 
                           es_administrador, 'admin' as tipo
                    FROM Empleados 
                    WHERE email = ? AND password_hash = ? AND activo = 1
                """
            else:
                query = """
                    SELECT cliente_id as id, nombre_completo, email, 
                           NULL as puesto, 0 as es_administrador, 'client' as tipo
                    FROM Clientes 
                    WHERE email = ? AND password_hash = ? AND activo = 1
                """
            
            result = execute_query(query, (email, hashed_password))
            
            if result:
                user = result[0]
                # Agregar campos adicionales para compatibilidad
                if is_admin:
                    user['empleado_id'] = user['id']
                else:
                    user['cliente_id'] = user['id']
                return user
            
            return None
            
        except Exception as e:
            logger.error(f"Error en autenticación: {e}")
            return None
    
    @staticmethod
    def get_by_id(user_id, is_admin=False):
        """Obtener usuario por ID"""
        try:
            if is_admin:
                query = """
                    SELECT empleado_id, nombre_completo, email, puesto, es_administrador
                    FROM Empleados 
                    WHERE empleado_id = ? AND activo = 1
                """
            else:
                query = """
                    SELECT cliente_id, nombre_completo, email, telefono, direccion
                    FROM Clientes 
                    WHERE cliente_id = ? AND activo = 1
                """
            
            result = execute_query(query, (user_id,))
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Error obteniendo usuario: {e}")
            return None