import sqlite3
from flask import g
import os

# Elimina todas las importaciones problemáticas y usa esto:

def get_db_connection():
    """Conexión SQLite para desarrollo"""
    conn = sqlite3.connect('rusteze.db')
    conn.row_factory = sqlite3.Row
    return conn

def execute_query(query, params=None):
    """Ejecutar consultas SQL"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # Si es SELECT, retornar resultados
        if query.strip().upper().startswith('SELECT'):
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            return results
        else:
            conn.commit()
            return {"success": True}
            
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_database():
    """Inicializar la base de datos SQLite con la estructura necesaria"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabla Empleados
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Empleados (
            empleado_id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_completo TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            puesto TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            fecha_contratacion DATE DEFAULT CURRENT_DATE,
            activo BOOLEAN DEFAULT 1,
            es_administrador BOOLEAN DEFAULT 0
        )
    ''')
    
    # Tabla Clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Clientes (
            cliente_id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_completo TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            telefono TEXT,
            direccion TEXT,
            tipo_documento TEXT NOT NULL,
            numero_documento TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
            activo BOOLEAN DEFAULT 1
        )
    ''')
    
    # Tabla Vehiculos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Vehiculos (
            vehiculo_id INTEGER PRIMARY KEY AUTOINCREMENT,
            marca TEXT NOT NULL,
            modelo TEXT NOT NULL,
            anio INTEGER NOT NULL,
            precio DECIMAL(10,2) NOT NULL,
            color TEXT NOT NULL,
            tipo TEXT NOT NULL,
            estado_disponibilidad TEXT DEFAULT 'Disponible',
            imagen_url TEXT,
            descripcion TEXT,
            fecha_ingreso DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla Ventas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Ventas (
            venta_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            empleado_id INTEGER NOT NULL,
            fecha_venta DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_venta DECIMAL(10,2) NOT NULL,
            metodo_pago TEXT NOT NULL,
            estado_venta TEXT DEFAULT 'Activa',
            FOREIGN KEY (cliente_id) REFERENCES Clientes (cliente_id),
            FOREIGN KEY (empleado_id) REFERENCES Empleados (empleado_id)
        )
    ''')
    
    # Tabla Detalle_Ventas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Detalle_Ventas (
            detalle_id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER NOT NULL,
            vehiculo_id INTEGER NOT NULL,
            precio_unitario DECIMAL(10,2) NOT NULL,
            cantidad INTEGER DEFAULT 1,
            FOREIGN KEY (venta_id) REFERENCES Ventas (venta_id) ON DELETE CASCADE,
            FOREIGN KEY (vehiculo_id) REFERENCES Vehiculos (vehiculo_id)
        )
    ''')
    
    # Insertar datos de prueba
    cursor.execute('''
        INSERT OR IGNORE INTO Empleados (nombre_completo, email, puesto, password_hash, es_administrador)
        VALUES 
        ('Administrador Principal', 'admin@rusteze.com', 'Gerente', 'admin123', 1),
        ('Vendedor Ejemplo', 'vendedor@rusteze.com', 'Vendedor', 'user123', 0)
    ''')
    
    cursor.execute('''
        INSERT OR IGNORE INTO Clientes (nombre_completo, email, telefono, tipo_documento, numero_documento, password_hash)
        VALUES 
        ('Cliente Demo', 'cliente@ejemplo.com', '555-1234', 'INE', 'ABC123456', 'cliente123')
    ''')
    
    cursor.execute('''
        INSERT OR IGNORE INTO Vehiculos (marca, modelo, anio, precio, color, tipo, descripcion, imagen_url)
        VALUES 
        ('Toyota', 'Corolla', 2024, 450000.00, 'Blanco', 'Sedan', 'Automóvil familiar confiable', '/static/images/vehicles/corolla.jpg'),
        ('Honda', 'CR-V', 2023, 620000.00, 'Plata', 'SUV', 'SUV espaciosa para la familia', '/static/images/vehicles/crv.jpg'),
        ('Ford', 'Mustang', 2023, 1100000.00, 'Rojo', 'Deportivo', 'Leyenda americana con potencia', '/static/images/vehicles/mustang.jpg')
    ''')
    
    conn.commit()
    conn.close()

class User:
    """Clase para manejar usuarios"""
    
    @staticmethod
    def authenticate(email, password, is_admin=False):
        """Autenticar usuario"""
        if is_admin:
            query = """
                SELECT empleado_id, nombre_completo, email, puesto, es_administrador 
                FROM Empleados 
                WHERE email = ? AND password_hash = ? AND activo = 1
            """
        else:
            query = """
                SELECT cliente_id, nombre_completo, email 
                FROM Clientes 
                WHERE email = ? AND password_hash = ? AND activo = 1
            """
        
        try:
            result = execute_query(query, (email, password))
            if result:
                return result[0]
            return None
        except Exception as e:
            print(f"Error en autenticación: {e}")
            return None