"""
Conexión unificada a SQL Server 2022 Express.
Elimina todas las referencias a SQLite.
"""

import pyodbc
from flask import g
import logging
from contextlib import contextmanager
from werkzeug.security import generate_password_hash, check_password_hash

logger = logging.getLogger(__name__)


class SQLServerConnection:
    """Manejador de conexión unificado a SQL Server Express"""

    @staticmethod
    def get_connection():
        """Obtener conexión desde el contexto de Flask"""
        if "sqlserver_conn" not in g:
            try:
                # Conexión a la instancia local SQLEXPRESS y BD RustEze_Agency
                connection_string = (
                    "DRIVER={ODBC Driver 17 for SQL Server};"
                    "SERVER=localhost\\SQLEXPRESS;"
                    "DATABASE=RustEze_Agency;"
                    "Trusted_Connection=yes;"
                )

                g.sqlserver_conn = pyodbc.connect(connection_string)
                g.sqlserver_conn.autocommit = False
                logger.info("✅ Conexión SQL Server Express establecida")

            except pyodbc.Error as e:
                logger.error(f"❌ Error conexión SQL Server: {e}")
                raise ConnectionError(f"No se pudo conectar a SQL Server: {e}")

        return g.sqlserver_conn

    @staticmethod
    def close_connection(e=None):
        """Cerrar conexión al final del contexto"""
        conn = g.pop("sqlserver_conn", None)
        if conn is not None:
            try:
                conn.close()
                logger.debug("🔌 Conexión SQL Server cerrada")
            except Exception:
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
    Ejecutar consulta SQL con manejo de errores.
    Devuelve lista de dicts si es SELECT, o dict con rows_affected en DML.
    """
    try:
        with get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if fetch and query.strip().upper().startswith("SELECT"):
                columns = [col[0] for col in cursor.description] if cursor.description else []
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                return results
            else:
                cursor.connection.commit()
                return {"success": True, "rows_affected": cursor.rowcount}

    except pyodbc.Error as e:
        logger.error(f"Error en execute_query: {e}")

        try:
            if "cursor" in locals() and cursor.connection:
                cursor.connection.rollback()
        except Exception:
            pass

        # Registrar error en auditoría (si la tabla existe)
        try:
            error_query = """
                INSERT INTO Auditoria_Errores (procedimiento, mensaje_error, numero_error, usuario)
                VALUES (?, ?, ?, ?)
            """
            with get_cursor() as error_cursor:
                error_cursor.execute(
                    error_query,
                    ("execute_query", str(e), 0, "SYSTEM"),
                )
                error_cursor.connection.commit()
        except Exception:
            pass

        raise e


def call_stored_procedure(proc_name, params=None):
    """
    Ejecutar procedimiento almacenado con parámetros en dbo de RustEze_Agency.
    IMPORTANTE: siempre hacer COMMIT aunque el SP devuelva filas.
    """
    try:
        with get_cursor() as cursor:
            if params:
                placeholders = ', '.join(['?'] * len(params))
                sql = f"EXEC dbo.{proc_name} {placeholders}"
                cursor.execute(sql, params)
            else:
                sql = f"EXEC dbo.{proc_name}"
                cursor.execute(sql)

            rows = None
            if cursor.description:
                # El SP devuelve un resultset (como sp_RegistrarVenta)
                columns = [c[0] for c in cursor.description]
                rows = [dict(zip(columns, r)) for r in cursor.fetchall()]

            # AQUÍ el cambio importante: SIEMPRE COMMIT
            cursor.connection.commit()

            if rows is not None:
                return rows
            else:
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
        except Exception:
            pass

        raise e

def init_app(app):
    """Inicializar extensión con Flask app"""
    app.teardown_appcontext(SQLServerConnection.close_connection)

    # Verificar conexión al inicio
    with app.app_context():
        try:
            test = execute_query("SELECT @@VERSION AS version")
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
    def hash_password(password: str) -> str:
        """Generar hash seguro de contraseña."""
        return generate_password_hash(password)

    @staticmethod
    def authenticate(email, password, is_admin=False):
        """
        Autenticar usuario contra SQL Server.

        1) Busca por email y activo = 1.
        2) Compara contraseña con check_password_hash.
        """
        try:
            if is_admin:
                query = """
                    SELECT 
                        empleado_id AS id,
                        nombre_completo,
                        email,
                        puesto,
                        es_administrador,
                        password_hash
                    FROM Empleados
                    WHERE email = ? AND activo = 1
                """
            else:
                query = """
                    SELECT 
                        cliente_id AS id,
                        nombre_completo,
                        email,
                        telefono,
                        password_hash,
                        activo
                    FROM Clientes
                    WHERE email = ? AND activo = 1
                """

            rows = execute_query(query, (email,))
            if not rows:
                return None

            user = rows[0]

            # Validar contraseña
            if not check_password_hash(user["password_hash"], password):
                return None

            # No exponer hash
            user.pop("password_hash", None)

            # Campos de compatibilidad usados en la app
            if is_admin:
                user["empleado_id"] = user["id"]
                user["es_administrador"] = True
                user["tipo"] = "admin"
            else:
                user["cliente_id"] = user["id"]
                user["es_administrador"] = False
                user["tipo"] = "client"

            return user

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
