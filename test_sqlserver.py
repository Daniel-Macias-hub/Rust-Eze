import pyodbc

def test_connection():
    print("=== PRUEBA DE CONEXIÓN SQL SERVER EXPRESS ===\n")
    
    # Diferentes cadenas de conexión a probar
    connection_strings = [
        # Opción 1: Con instancia SQLEXPRESS
        (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=localhost\\SQLEXPRESS;"
            "DATABASE=RustEze_Agency;"
            "Trusted_Connection=yes;"
        ),
        # Opción 2: Con punto (local)
        (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=.\\SQLEXPRESS;"
            "DATABASE=RustEze_Agency;"
            "Trusted_Connection=yes;"
        ),
        # Opción 3: Con (local)
        (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=(local)\\SQLEXPRESS;"
            "DATABASE=RustEze_Agency;"
            "Trusted_Connection=yes;"
        )
    ]
    
    for i, conn_str in enumerate(connection_strings, 1):
        print(f"Intentando conexión {i}:")
        print(f"  Cadena: {conn_str[:80]}...")
        
        try:
            conn = pyodbc.connect(conn_str)
            print("  ✅ CONEXIÓN EXITOSA")
            
            # Verificar tablas
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            print(f"  Tablas encontradas: {len(tables)}")
            
            # Mostrar tablas importantes
            important_tables = ['Clientes', 'Vehiculos', 'Ventas', 'Auditoria_Ventas']
            for table in important_tables:
                if table in tables:
                    print(f"    ✓ {table}")
                else:
                    print(f"    ✗ {table} (FALTANTE)")
            
            cursor.close()
            conn.close()
            print()
            
            # Si una funciona, usala
            if i == 1:
                # Guardar la cadena exitosa
                with open('.env', 'a') as f:
                    f.write(f'\nSUCCESSFUL_CONNECTION_STRING={conn_str}\n')
            
        except pyodbc.Error as e:
            print(f"  ❌ ERROR: {e}")
            print()
            continue
    
    print("\n=== RECOMENDACIÓN ===")
    print("Usa la primera cadena que funcionó en tu archivo .env")

if __name__ == "__main__":
    test_connection()