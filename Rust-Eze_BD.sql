/*
==========================================================================
RUST-EZE - BASE DE DATOS DEFINITIVA OPTIMIZADA
Fecha: Noviembre 2025
==========================================================================
*/

-- ========================================================================================================================
-- 1. CREACIÓN DE BASE DE DATOS
-- ========================================================================================================================
USE master;
GO

IF DB_ID('RustEze_Agency') IS NOT NULL
BEGIN
    ALTER DATABASE RustEze_Agency SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE RustEze_Agency;
END
GO

CREATE DATABASE RustEze_Agency;
GO

USE RustEze_Agency;
GO
-- ========================================================================================================================
-- 2. SECUENCIAS (Requisito 4.2)
-- ========================================================================================================================
CREATE SEQUENCE dbo.Seq_Clientes START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE dbo.Seq_Vehiculos START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE dbo.Seq_Empleados START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE dbo.Seq_Ventas START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE dbo.Seq_DetalleVentas START WITH 1 INCREMENT BY 1;
GO
-- ========================================================================================================================
-- 3. TABLAS PRINCIPALES
-- ========================================================================================================================
CREATE TABLE dbo.Clientes (
    cliente_id INT NOT NULL DEFAULT (NEXT VALUE FOR dbo.Seq_Clientes),
    nombre_completo VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    direccion VARCHAR(150),
    tipo_documento VARCHAR(20) NOT NULL,
    numero_documento VARCHAR(30) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    fecha_registro DATETIME DEFAULT GETDATE(),
    activo BIT DEFAULT 1,
    
    CONSTRAINT PK_Clientes PRIMARY KEY (cliente_id),
    CONSTRAINT UQ_Clientes_Email UNIQUE (email),
    CONSTRAINT UQ_Clientes_Documento UNIQUE (tipo_documento, numero_documento)
);

CREATE TABLE dbo.Empleados (
    empleado_id INT NOT NULL DEFAULT (NEXT VALUE FOR dbo.Seq_Empleados),
    nombre_completo VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    puesto VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    fecha_contratacion DATE DEFAULT GETDATE(),
    activo BIT DEFAULT 1,
    es_administrador BIT DEFAULT 0,
    
    CONSTRAINT PK_Empleados PRIMARY KEY (empleado_id),
    CONSTRAINT UQ_Empleados_Email UNIQUE (email),
    CONSTRAINT CHK_Empleados_Puesto CHECK (puesto IN ('Gerente', 'Vendedor', 'Administrativo'))
);

CREATE TABLE dbo.Vehiculos (
    vehiculo_id INT NOT NULL DEFAULT (NEXT VALUE FOR dbo.Seq_Vehiculos),
    marca VARCHAR(50) NOT NULL,
    modelo VARCHAR(50) NOT NULL,
    anio INT NOT NULL,
    precio DECIMAL(18,2) NOT NULL,
    color VARCHAR(30) NOT NULL,
    tipo VARCHAR(30) NOT NULL,
    estado_disponibilidad VARCHAR(20) DEFAULT 'Disponible',
    imagen_url VARCHAR(255),
    descripcion TEXT,
    fecha_ingreso DATETIME DEFAULT GETDATE(),
    
    CONSTRAINT PK_Vehiculos PRIMARY KEY (vehiculo_id),
    CONSTRAINT CHK_Vehiculos_Precio CHECK (precio > 0),
    CONSTRAINT CHK_Vehiculos_Anio CHECK (anio BETWEEN 2000 AND YEAR(GETDATE()) + 1),
    CONSTRAINT CHK_Vehiculos_Estado CHECK (estado_disponibilidad IN ('Disponible', 'Vendido', 'Reservado', 'Mantenimiento'))
);

CREATE TABLE dbo.Ventas (
    venta_id INT NOT NULL DEFAULT (NEXT VALUE FOR dbo.Seq_Ventas),
    cliente_id INT NOT NULL,
    empleado_id INT NOT NULL,
    fecha_venta DATETIME DEFAULT GETDATE(),
    total_venta DECIMAL(18,2) NOT NULL,
    metodo_pago VARCHAR(50) NOT NULL,
    estado_venta VARCHAR(20) DEFAULT 'Activa',
    
    CONSTRAINT PK_Ventas PRIMARY KEY (venta_id),
    CONSTRAINT FK_Ventas_Clientes FOREIGN KEY (cliente_id) REFERENCES dbo.Clientes(cliente_id),
    CONSTRAINT FK_Ventas_Empleados FOREIGN KEY (empleado_id) REFERENCES dbo.Empleados(empleado_id),
    CONSTRAINT CHK_Ventas_Estado CHECK (estado_venta IN ('Activa', 'Cancelada', 'Finalizada')),
    CONSTRAINT CHK_Ventas_MetodoPago CHECK (metodo_pago IN ('Efectivo', 'Tarjeta', 'Transferencia', 'Financiamiento'))
);

CREATE TABLE dbo.Detalle_Ventas (
    detalle_id INT NOT NULL DEFAULT (NEXT VALUE FOR dbo.Seq_DetalleVentas),
    venta_id INT NOT NULL,
    vehiculo_id INT NOT NULL,
    precio_unitario DECIMAL(18,2) NOT NULL,
    cantidad INT DEFAULT 1,
    
    CONSTRAINT PK_DetalleVentas PRIMARY KEY (detalle_id),
    CONSTRAINT FK_Detalle_Ventas FOREIGN KEY (venta_id) REFERENCES dbo.Ventas(venta_id) ON DELETE CASCADE,
    CONSTRAINT FK_Detalle_Vehiculos FOREIGN KEY (vehiculo_id) REFERENCES dbo.Vehiculos(vehiculo_id),
    CONSTRAINT CHK_Detalle_Cantidad CHECK (cantidad > 0)
);
-- ========================================================================================================================
-- 4. TABLAS DE AUDITORÍA (Requisito 4.1.6)
-- ========================================================================================================================
--AUDITORIA VENTAS --

CREATE TABLE dbo.Auditoria_Ventas (
    audit_id INT IDENTITY(1,1) PRIMARY KEY,
    accion VARCHAR(10) NOT NULL,
    venta_id INT,
    usuario VARCHAR(100),
    fecha_evento DATETIME DEFAULT GETDATE(),
    datos_anteriores NVARCHAR(MAX),
    datos_nuevos NVARCHAR(MAX)
);

CREATE TABLE dbo.Auditoria_Ventas_Insercion (
    audit_id INT IDENTITY(1,1) PRIMARY KEY,
    venta_id INT NOT NULL,
    cliente_id INT NOT NULL,
    empleado_id INT NOT NULL,
    fecha_venta DATETIME,
    total_venta DECIMAL(18,2),
    metodo_pago VARCHAR(50),
    estado_venta VARCHAR(20),
    usuario VARCHAR(100),
    fecha_insercion DATETIME DEFAULT GETDATE()
);

CREATE TABLE dbo.Auditoria_Ventas_Actualizacion (
    audit_id INT IDENTITY(1,1) PRIMARY KEY,
    venta_id INT NOT NULL,
    cliente_id_anterior INT,
    empleado_id_anterior INT,
    fecha_venta_anterior DATETIME,
    total_venta_anterior DECIMAL(18,2),
    metodo_pago_anterior VARCHAR(50),
    estado_venta_anterior VARCHAR(20),
    cliente_id_nuevo INT,
    empleado_id_nuevo INT,
    fecha_venta_nueva DATETIME,
    total_venta_nueva DECIMAL(18,2),
    metodo_pago_nuevo VARCHAR(50),
    estado_venta_nuevo VARCHAR(20),
    usuario VARCHAR(100),
    fecha_actualizacion DATETIME DEFAULT GETDATE()
);

CREATE TABLE dbo.Auditoria_Ventas_Eliminacion (
    audit_id INT IDENTITY(1,1) PRIMARY KEY,
    venta_id INT NOT NULL,
    cliente_id INT NOT NULL,
    empleado_id INT NOT NULL,
    fecha_venta DATETIME,
    total_venta DECIMAL(18,2),
    metodo_pago VARCHAR(50),
    estado_venta VARCHAR(20),
    usuario VARCHAR(100),
    fecha_eliminacion DATETIME DEFAULT GETDATE()
);
-- ===========================================================================================
-- AUDITORIA VEHICULOS --
CREATE TABLE dbo.Auditoria_Vehiculos (
    audit_id INT IDENTITY(1,1) PRIMARY KEY,
    accion VARCHAR(10) NOT NULL,
    vehiculo_id INT,
    usuario VARCHAR(100),
    fecha_evento DATETIME DEFAULT GETDATE(),
    datos_anteriores NVARCHAR(MAX),
    datos_nuevos NVARCHAR(MAX)
);

CREATE TABLE dbo.Auditoria_Vehiculos_Insercion (
    audit_id INT IDENTITY(1,1) PRIMARY KEY,
    vehiculo_id INT NOT NULL,
    marca VARCHAR(50),
    modelo VARCHAR(50),
    anio INT,
    precio DECIMAL(18,2),
    color VARCHAR(30),
    tipo VARCHAR(30),
    estado_disponibilidad VARCHAR(20),
    usuario VARCHAR(100),
    fecha_insercion DATETIME DEFAULT GETDATE()
);

CREATE TABLE dbo.Auditoria_Vehiculos_Actualizacion (
    audit_id INT IDENTITY(1,1) PRIMARY KEY,
    vehiculo_id INT NOT NULL,
    marca_anterior VARCHAR(50),
    modelo_anterior VARCHAR(50),
    anio_anterior INT,
    precio_anterior DECIMAL(18,2),
    color_anterior VARCHAR(30),
    tipo_anterior VARCHAR(30),
    estado_disponibilidad_anterior VARCHAR(20),
    marca_nueva VARCHAR(50),
    modelo_nueva VARCHAR(50),
    anio_nueva INT,
    precio_nueva DECIMAL(18,2),
    color_nueva VARCHAR(30),
    tipo_nueva VARCHAR(30),
    estado_disponibilidad_nueva VARCHAR(20),
    usuario VARCHAR(100),
    fecha_actualizacion DATETIME DEFAULT GETDATE()
);

CREATE TABLE dbo.Auditoria_Vehiculos_Eliminacion (
    audit_id INT IDENTITY(1,1) PRIMARY KEY,
    vehiculo_id INT NOT NULL,
    marca VARCHAR(50),
    modelo VARCHAR(50),
    anio INT,
    precio DECIMAL(18,2),
    color VARCHAR(30),
    tipo VARCHAR(30),
    estado_disponibilidad VARCHAR(20),
    usuario VARCHAR(100),
    fecha_eliminacion DATETIME DEFAULT GETDATE()
);
-- ===========================================================================================
-- AUDITORIA ERRORES --
CREATE TABLE dbo.Auditoria_Errores (
    error_id INT IDENTITY(1,1) PRIMARY KEY,
    procedimiento VARCHAR(100),
    mensaje_error NVARCHAR(4000),
    numero_error INT,
    usuario VARCHAR(100),
    fecha_error DATETIME DEFAULT GETDATE()
);
-- ========================================================================================================================
-- 5. ÍNDICES (Requisito 7)
-- ========================================================================================================================
CREATE UNIQUE INDEX IX_Clientes_Email ON dbo.Clientes(email);
CREATE UNIQUE INDEX IX_Clientes_Documento ON dbo.Clientes(tipo_documento, numero_documento);
CREATE INDEX IX_Vehiculos_Marca_Modelo ON dbo.Vehiculos(marca, modelo);
CREATE INDEX IX_Vehiculos_Estado ON dbo.Vehiculos(estado_disponibilidad);
CREATE INDEX IX_Vehiculos_Precio ON dbo.Vehiculos(precio);
CREATE INDEX IX_Ventas_Fecha ON dbo.Ventas(fecha_venta);
CREATE INDEX IX_Ventas_Estado ON dbo.Ventas(estado_venta);
CREATE INDEX IX_Ventas_Cliente ON dbo.Ventas(cliente_id);
CREATE INDEX IX_Auditoria_Ventas_Fecha ON dbo.Auditoria_Ventas(fecha_evento);
CREATE INDEX IX_Auditoria_Vehiculos_Fecha ON dbo.Auditoria_Vehiculos(fecha_evento);
CREATE INDEX IX_Ventas_Cliente_Fecha ON dbo.Ventas(cliente_id, fecha_venta DESC);
CREATE INDEX IX_Vehiculos_Tipo_Precio ON dbo.Vehiculos(tipo, precio);
CREATE INDEX IX_Auditoria_VentasIns_Fecha ON dbo.Auditoria_Ventas_Insercion(fecha_insercion);
CREATE INDEX IX_Auditoria_VentasAct_Fecha ON dbo.Auditoria_Ventas_Actualizacion(fecha_actualizacion);
CREATE INDEX IX_Auditoria_VentasDel_Fecha ON dbo.Auditoria_Ventas_Eliminacion(fecha_eliminacion);
GO

USE RustEze_Agency;
GO
-- ========================================================================================================================
-- 6. TRIGGERS (Requisito 1)
-- ========================================================================================================================
-- Trigger de validación de disponibilidad
CREATE OR ALTER TRIGGER dbo.trg_ValidarDisponibilidadVehiculo
ON dbo.Detalle_Ventas
INSTEAD OF INSERT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @vehiculo_id INT;
    DECLARE @estado VARCHAR(20);
    
    SELECT @vehiculo_id = i.vehiculo_id 
    FROM inserted i;
    
    SELECT @estado = estado_disponibilidad 
    FROM dbo.Vehiculos 
    WHERE vehiculo_id = @vehiculo_id;
    
    IF @estado != 'Disponible'
    BEGIN
        RAISERROR('Error: El vehículo no está disponible para la venta.', 16, 1);
        RETURN;
    END
    
    -- Si está disponible, proceder con la inserción
    INSERT INTO dbo.Detalle_Ventas (venta_id, vehiculo_id, precio_unitario, cantidad)
    SELECT venta_id, vehiculo_id, precio_unitario, cantidad
    FROM inserted;
END;
GO

-- Trigger de auditoría para Ventas (Inserciones)
CREATE OR ALTER TRIGGER dbo.trg_Auditoria_Ventas_Insercion
ON dbo.Ventas
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    
    INSERT INTO dbo.Auditoria_Ventas_Insercion 
        (venta_id, cliente_id, empleado_id, fecha_venta, total_venta, metodo_pago, estado_venta, usuario)
    SELECT 
        i.venta_id, i.cliente_id, i.empleado_id, i.fecha_venta, i.total_venta, 
        i.metodo_pago, i.estado_venta, SYSTEM_USER
    FROM inserted i;
END;
GO

-- Trigger de auditoría para Ventas (Actualizaciones)
CREATE OR ALTER TRIGGER dbo.trg_Auditoria_Ventas_Actualizacion
ON dbo.Ventas
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    INSERT INTO dbo.Auditoria_Ventas_Actualizacion 
        (venta_id, cliente_id_anterior, empleado_id_anterior, fecha_venta_anterior, 
         total_venta_anterior, metodo_pago_anterior, estado_venta_anterior,
         cliente_id_nuevo, empleado_id_nuevo, fecha_venta_nueva, 
         total_venta_nueva, metodo_pago_nuevo, estado_venta_nuevo, usuario)
    SELECT 
        i.venta_id, d.cliente_id, d.empleado_id, d.fecha_venta, d.total_venta, 
        d.metodo_pago, d.estado_venta,
        i.cliente_id, i.empleado_id, i.fecha_venta, i.total_venta, 
        i.metodo_pago, i.estado_venta, SYSTEM_USER
    FROM inserted i
    INNER JOIN deleted d ON i.venta_id = d.venta_id;
END;
GO

-- Trigger de auditoría para Vehículos (Inserciones)
CREATE OR ALTER TRIGGER dbo.trg_Auditoria_Vehiculos_Insercion
ON dbo.Vehiculos
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    
    INSERT INTO dbo.Auditoria_Vehiculos_Insercion 
        (vehiculo_id, marca, modelo, anio, precio, color, tipo, estado_disponibilidad, usuario)
    SELECT 
        i.vehiculo_id, i.marca, i.modelo, i.anio, i.precio, i.color, 
        i.tipo, i.estado_disponibilidad, SYSTEM_USER
    FROM inserted i;
END;
GO
-- ========================================================================================================================
-- 7. PROCEDIMIENTOS ALMACENADOS (Requisito 3 y 8)
-- ========================================================================================================================
CREATE OR ALTER PROCEDURE dbo.sp_RegistrarVenta
    @cliente_id INT,
    @empleado_id INT,
    @vehiculo_id INT,
    @metodo_pago VARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @precio DECIMAL(18,2);
    DECLARE @estado VARCHAR(20);
    DECLARE @nueva_venta_id INT;
    DECLARE @nombre_vehiculo VARCHAR(100);

    BEGIN TRY
        BEGIN TRANSACTION;

        -- Validaciones (Requisito 8: TRY/CATCH)
        IF NOT EXISTS (SELECT 1 FROM dbo.Clientes WHERE cliente_id = @cliente_id AND activo = 1)
            THROW 50002, 'Cliente no existe o está inactivo.', 1;

        IF NOT EXISTS (SELECT 1 FROM dbo.Empleados WHERE empleado_id = @empleado_id AND activo = 1)
            THROW 50003, 'Empleado no existe o está inactivo.', 1;

        SELECT @precio = precio, @estado = estado_disponibilidad,
               @nombre_vehiculo = marca + ' ' + modelo
        FROM dbo.Vehiculos 
        WHERE vehiculo_id = @vehiculo_id;

        IF @precio IS NULL
            THROW 50004, 'Vehículo no encontrado.', 1;

        IF @estado != 'Disponible'
            THROW 50005, 'El vehículo no está disponible para la venta.', 1;

        -- Insertar venta (Requisito 5: Secuencia)
        INSERT INTO dbo.Ventas (cliente_id, empleado_id, total_venta, metodo_pago)
        VALUES (@cliente_id, @empleado_id, @precio, @metodo_pago);

        SET @nueva_venta_id = SCOPE_IDENTITY();

        -- Insertar detalle
        INSERT INTO dbo.Detalle_Ventas (venta_id, vehiculo_id, precio_unitario)
        VALUES (@nueva_venta_id, @vehiculo_id, @precio);

        -- Actualizar estado del vehículo
        UPDATE dbo.Vehiculos 
        SET estado_disponibilidad = 'Vendido' 
        WHERE vehiculo_id = @vehiculo_id;

        -- Auditoría automática (Requisito 1)
        INSERT INTO dbo.Auditoria_Ventas_Insercion 
            (venta_id, cliente_id, empleado_id, fecha_venta, total_venta, metodo_pago, estado_venta, usuario)
        SELECT 
            @nueva_venta_id, @cliente_id, @empleado_id, GETDATE(), @precio, @metodo_pago, 'Activa', SYSTEM_USER;

        COMMIT TRANSACTION;
        
        SELECT 
            'Éxito' AS resultado,
            @nueva_venta_id AS venta_id,
            'Venta registrada correctamente para ' + @nombre_vehiculo AS mensaje;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        
        -- Registrar error (Requisito 8)
        INSERT INTO dbo.Auditoria_Errores (procedimiento, mensaje_error, numero_error, usuario)
        VALUES ('sp_RegistrarVenta', ERROR_MESSAGE(), ERROR_NUMBER(), SYSTEM_USER);
        
        THROW;
    END CATCH
END;
GO

-- Procedimiento sp_CancelarVenta CORREGIDO
CREATE OR ALTER PROCEDURE dbo.sp_CancelarVenta
    @venta_id INT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @estado_actual VARCHAR(20);
    DECLARE @vehiculo_id INT;
    DECLARE @nombre_vehiculo VARCHAR(100);

    BEGIN TRY
        BEGIN TRANSACTION;

        SELECT @estado_actual = estado_venta
        FROM dbo.Ventas
        WHERE venta_id = @venta_id;

        IF @estado_actual IS NULL
            THROW 50006, 'Venta no encontrada.', 1;

        IF @estado_actual != 'Activa'
            THROW 50007, 'Solo se pueden cancelar ventas activas.', 1;

        -- Obtener vehículo asociado
        SELECT @vehiculo_id = dv.vehiculo_id, 
               @nombre_vehiculo = v.marca + ' ' + v.modelo
        FROM dbo.Detalle_Ventas dv
        JOIN dbo.Vehiculos v ON dv.vehiculo_id = v.vehiculo_id
        WHERE dv.venta_id = @venta_id;

        -- Registrar auditoría antes de cambiar
        INSERT INTO dbo.Auditoria_Ventas_Actualizacion 
            (venta_id, cliente_id_anterior, empleado_id_anterior, estado_venta_anterior,
             estado_venta_nuevo, usuario)
        SELECT 
            @venta_id, v.cliente_id, v.empleado_id, 'Activa',
            'Cancelada', SYSTEM_USER
        FROM dbo.Ventas v
        WHERE v.venta_id = @venta_id;

        -- Cancelar venta
        UPDATE dbo.Ventas
        SET estado_venta = 'Cancelada'
        WHERE venta_id = @venta_id;

        -- Liberar vehículo
        UPDATE dbo.Vehiculos 
        SET estado_disponibilidad = 'Disponible' 
        WHERE vehiculo_id = @vehiculo_id;

        COMMIT TRANSACTION;
        
        SELECT 
            'Éxito' AS resultado, 
            'Venta #' + CAST(@venta_id AS VARCHAR) + ' cancelada. Vehículo ' + @nombre_vehiculo + ' disponible nuevamente.' AS mensaje;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        
        INSERT INTO dbo.Auditoria_Errores (procedimiento, mensaje_error, numero_error, usuario)
        VALUES ('sp_CancelarVenta', ERROR_MESSAGE(), ERROR_NUMBER(), SYSTEM_USER);
        
        THROW;
    END CATCH
END;
GO

-- Procedimientos adicionales requeridos
CREATE OR ALTER PROCEDURE dbo.sp_HistorialComprasCliente
    @cliente_id INT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        v.venta_id,
        v.fecha_venta,
        v.total_venta,
        v.metodo_pago,
        v.estado_venta,
        ve.marca,
        ve.modelo,
        ve.anio,
        ve.color,
        ve.tipo,
        e.nombre_completo as vendedor
    FROM dbo.Ventas v
    JOIN dbo.Detalle_Ventas dv ON v.venta_id = dv.venta_id
    JOIN dbo.Vehiculos ve ON dv.vehiculo_id = ve.vehiculo_id
    JOIN dbo.Empleados e ON v.empleado_id = e.empleado_id
    WHERE v.cliente_id = @cliente_id
    ORDER BY v.fecha_venta DESC;
END;
GO
-- ========================================================================================================================
-- 8. DATOS INICIALES
-- ========================================================================================================================
INSERT INTO dbo.Empleados (nombre_completo, email, puesto, password_hash, es_administrador) 
VALUES 
('Administrador Principal', 'admin@rusteze.com', 'Gerente', 'hashed_password_123', 1),
('Vendedor Ejemplo', 'vendedor@rusteze.com', 'Vendedor', 'hashed_password_123', 0);

INSERT INTO dbo.Clientes (nombre_completo, email, telefono, tipo_documento, numero_documento, password_hash)
VALUES 
('Cliente Demo', 'cliente@ejemplo.com', '555-1234', 'INE', 'ABC123456', 'hashed_password_123');

INSERT INTO dbo.Vehiculos (marca, modelo, anio, precio, color, tipo, descripcion, imagen_url)
VALUES
('Toyota', 'Corolla', 2024, 450000.00, 'Blanco', 'Sedan', 'Automóvil familiar confiable y eficiente', '/static/images/vehicles/corolla.jpg'),
('Honda', 'CR-V', 2023, 620000.00, 'Plata', 'SUV', 'SUV espaciosa y versátil para la familia', '/static/images/vehicles/crv.jpg'),
('Ford', 'Mustang', 2023, 1100000.00, 'Rojo', 'Deportivo', 'Leyenda americana con potencia y estilo', '/static/images/vehicles/mustang.jpg');
-- ========================================================================================================================
-- 9. PRUEBAS FUNCIONALES
-- ========================================================================================================================
PRINT '=== INICIANDO PRUEBAS FUNCIONALES ===';
-- ========================================================================================================================
-- Prueba 1: Venta exitosa
-- ========================================================================================================================
BEGIN TRY
    EXEC dbo.sp_RegistrarVenta @cliente_id = 1, @empleado_id = 2, @vehiculo_id = 1, @metodo_pago = 'Tarjeta';
    PRINT '✓ Prueba 1 PASADA: Venta registrada exitosamente';
END TRY
BEGIN CATCH
    PRINT '✗ Prueba 1 FALLADA: ' + ERROR_MESSAGE();
END CATCH
-- ========================================================================================================================
-- Prueba 2: Intentar vender vehículo ya vendido (debe fallar)
-- ========================================================================================================================
BEGIN TRY
    EXEC dbo.sp_RegistrarVenta @cliente_id = 1, @empleado_id = 2, @vehiculo_id = 1, @metodo_pago = 'Efectivo';
    PRINT '✗ Prueba 2 FALLADA: Debió generar error por vehículo no disponible';
END TRY
BEGIN CATCH
    PRINT '✓ Prueba 2 PASADA: Correctamente evitó vender vehículo no disponible';
END CATCH
-- ========================================================================================================================
-- Prueba 3: Cancelar venta
-- ========================================================================================================================
BEGIN TRY
    EXEC dbo.sp_CancelarVenta @venta_id = 1;
    PRINT '✓ Prueba 3 PASADA: Venta cancelada exitosamente';
END TRY
BEGIN CATCH
    PRINT '✗ Prueba 3 FALLADA: ' + ERROR_MESSAGE();
END CATCH

PRINT '=== PRUEBAS COMPLETADAS ===';
GO

-- Verificar si la base de datos RustEze_Agency existe
SELECT name FROM sys.databases WHERE name = 'RustEze_Agency';


USE RustEze_Agency;
GO

-- Verificar procedimientos almacenados
SELECT 
    name as 'Procedimiento',
    create_date as 'Creado',
    modify_date as 'Modificado'
FROM sys.procedures
WHERE name IN ('sp_RegistrarVenta', 'sp_CancelarVenta')
ORDER BY name;
GO

-- Verificar triggers
SELECT 
    t.name as 'Trigger',
    OBJECT_NAME(t.parent_id) as 'Tabla',
    t.create_date as 'Creado'
FROM sys.triggers t
WHERE t.is_ms_shipped = 0
ORDER BY t.name;
GO