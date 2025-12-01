"""
Conexión a SQL Server 2022 Express con manejo de procedimientos almacenados
"""

import pyodbc
from flask import g, current_app
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class SQLServerConnection:
    """Manejador de conexión a SQL Server Express"""
    
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
                logger.info("✅ Conexión SQL Server Express establecida")
                
            except pyodbc.Error as e:
                logger.error(f"❌ Error conexión SQL Server: {e}")
                raise ConnectionError(f"No se pudo conectar a SQL Server: {e}")
                
        return g.sqlserver_conn
    
    @staticmethod
    def close_connection(e=None):
        """Cerrar conexión al final del contexto"""
        conn = g.pop('sqlserver_conn', None)
        if conn is not None:
            conn.close()
            logger.debug("🔌 Conexión SQL Server cerrada")

@contextmanager
def get_cursor():
    """Context manager para manejo automático de cursor"""
    conn = SQLServerConnection.get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
    finally:
        cursor.close()

def execute_query(query, params=None, fetch=True):
    """
    Ejecutar consulta SQL con manejo de errores y TRY/CATCH implícito
    """
    try:
        with get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch and query.strip().upper().startswith('SELECT'):
                columns = [column[0] for column in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                return results
            else:
                cursor.connection.commit()
                return {"success": True, "rows_affected": cursor.rowcount}
                
    except pyodbc.Error as e:
        logger.error(f"Error en execute_query: {e}")
        
        # Intentar registrar error en auditoría
        try:
            with get_cursor() as error_cursor:
                error_query = """
                INSERT INTO Auditoria_Errores (procedimiento, mensaje_error, numero_error, usuario)
                VALUES (?, ?, ?, ?)
                """
                error_cursor.execute(error_query, ('execute_query', str(e), 0, 'SYSTEM'))
                error_cursor.connection.commit()
        except:
            pass  # Si falla registrar error, al menos logueamos
            
        raise e

def call_stored_procedure(proc_name, params=None):
    """
    Ejecutar procedimiento almacenado con parámetros
    """
    try:
        with get_cursor() as cursor:
            if params:
                placeholders = ', '.join(['?'] * len(params))
                cursor.execute(f"EXEC {proc_name} {placeholders}", params)
            else:
                cursor.execute(f"EXEC {proc_name}")
            
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
            with get_cursor() as error_cursor:
                error_query = """
                INSERT INTO Auditoria_Errores (procedimiento, mensaje_error, numero_error, usuario)
                VALUES (?, ?, ?, ?)
                """
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
            
            # Verificar estructura básica
            tables = execute_query("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME IN ('Clientes', 'Vehiculos', 'Ventas')
            """)
            
            if len(tables) >= 3:
                logger.info(f"✅ Estructura básica verificada: {len(tables)} tablas principales")
            else:
                logger.warning(f"⚠️  Faltan tablas principales. Esperadas: 3, Encontradas: {len(tables)}")
                
        except Exception as e:
            logger.error(f"❌ Error inicialización SQL Server: {e}")
            raise