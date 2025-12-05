/*
==========================================================================
RUST-EZE - BASE DE DATOS DEFINITIVA OPTIMIZADA (VERSIÓN ACTUALIZADA)
Fecha: Diciembre 2025
==========================================================================
*/

-- ======================================================================
-- 1. RECREAR BASE DE DATOS
-- ======================================================================
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

-- ======================================================================
-- 2. SECUENCIAS (Requisito 4.2)
-- ======================================================================
CREATE SEQUENCE dbo.Seq_Clientes       START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE dbo.Seq_Vehiculos      START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE dbo.Seq_Empleados      START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE dbo.Seq_Ventas         START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE dbo.Seq_DetalleVentas  START WITH 1 INCREMENT BY 1;
GO

-- ======================================================================
-- 3. TABLAS PRINCIPALES
-- ======================================================================
CREATE TABLE dbo.Clientes (
    cliente_id       INT           NOT NULL DEFAULT (NEXT VALUE FOR dbo.Seq_Clientes),
    nombre_completo  VARCHAR(100)  NOT NULL,
    email            VARCHAR(100)  NOT NULL,
    telefono         VARCHAR(20),
    direccion        VARCHAR(150),
    tipo_documento   VARCHAR(20)   NOT NULL,
    numero_documento VARCHAR(30)   NOT NULL,
    password_hash    VARCHAR(255)  NOT NULL,
    fecha_registro   DATETIME      DEFAULT GETDATE(),
    activo           BIT           DEFAULT 1,

    CONSTRAINT PK_Clientes           PRIMARY KEY (cliente_id),
    CONSTRAINT UQ_Clientes_Email     UNIQUE (email),
    CONSTRAINT UQ_Clientes_Documento UNIQUE (tipo_documento, numero_documento)
);

CREATE TABLE dbo.Empleados (
    empleado_id      INT           NOT NULL DEFAULT (NEXT VALUE FOR dbo.Seq_Empleados),
    nombre_completo  VARCHAR(100)  NOT NULL,
    email            VARCHAR(100)  NOT NULL,
    puesto           VARCHAR(50)   NOT NULL,
    password_hash    VARCHAR(255)  NOT NULL,
    fecha_contratacion DATE        DEFAULT GETDATE(),
    activo           BIT           DEFAULT 1,
    es_administrador BIT           DEFAULT 0,

    CONSTRAINT PK_Empleados       PRIMARY KEY (empleado_id),
    CONSTRAINT UQ_Empleados_Email UNIQUE (email),
    CONSTRAINT CHK_Empleados_Puesto CHECK (puesto IN ('Gerente', 'Vendedor', 'Administrativo'))
);

CREATE TABLE dbo.Vehiculos (
    vehiculo_id          INT           NOT NULL DEFAULT (NEXT VALUE FOR dbo.Seq_Vehiculos),
    marca                VARCHAR(50)   NOT NULL,
    modelo               VARCHAR(50)   NOT NULL,
    anio                 INT           NOT NULL,
    precio               DECIMAL(18,2) NOT NULL,
    color                VARCHAR(30)   NOT NULL,
    tipo                 VARCHAR(30)   NOT NULL,
    estado_disponibilidad VARCHAR(20)  DEFAULT 'Disponible',
    imagen_url           VARCHAR(255),
    descripcion          TEXT,
    fecha_ingreso        DATETIME      DEFAULT GETDATE(),

    CONSTRAINT PK_Vehiculos            PRIMARY KEY (vehiculo_id),
    CONSTRAINT CHK_Vehiculos_Precio    CHECK (precio > 0),
    CONSTRAINT CHK_Vehiculos_Anio      CHECK (anio BETWEEN 2000 AND YEAR(GETDATE()) + 1),
    CONSTRAINT CHK_Vehiculos_Estado    CHECK (estado_disponibilidad IN ('Disponible', 'Vendido', 'Reservado', 'Mantenimiento'))
);

CREATE TABLE dbo.Ventas (
    venta_id      INT           NOT NULL DEFAULT (NEXT VALUE FOR dbo.Seq_Ventas),
    cliente_id    INT           NOT NULL,
    empleado_id   INT           NOT NULL,
    fecha_venta   DATETIME      DEFAULT GETDATE(),
    total_venta   DECIMAL(18,2) NOT NULL,
    metodo_pago   VARCHAR(50)   NOT NULL,
    estado_venta  VARCHAR(20)   DEFAULT 'Activa',

    CONSTRAINT PK_Ventas          PRIMARY KEY (venta_id),
    CONSTRAINT FK_Ventas_Clientes FOREIGN KEY (cliente_id)  REFERENCES dbo.Clientes(cliente_id),
    CONSTRAINT FK_Ventas_Empleados FOREIGN KEY (empleado_id) REFERENCES dbo.Empleados(empleado_id),
    CONSTRAINT CHK_Ventas_Estado  CHECK (estado_venta IN ('Activa', 'Cancelada', 'Finalizada')),
    CONSTRAINT CHK_Ventas_MetodoPago CHECK (metodo_pago IN ('Efectivo', 'Tarjeta', 'Transferencia', 'Financiamiento'))
);

CREATE TABLE dbo.Detalle_Ventas (
    detalle_id     INT           NOT NULL DEFAULT (NEXT VALUE FOR dbo.Seq_DetalleVentas),
    venta_id       INT           NOT NULL,
    vehiculo_id    INT           NOT NULL,
    precio_unitario DECIMAL(18,2) NOT NULL,
    cantidad       INT           DEFAULT 1,

    CONSTRAINT PK_DetalleVentas       PRIMARY KEY (detalle_id),
    CONSTRAINT FK_Detalle_Ventas      FOREIGN KEY (venta_id)    REFERENCES dbo.Ventas(venta_id) ON DELETE CASCADE,
    CONSTRAINT FK_Detalle_Vehiculos   FOREIGN KEY (vehiculo_id) REFERENCES dbo.Vehiculos(vehiculo_id),
    CONSTRAINT CHK_Detalle_Cantidad   CHECK (cantidad > 0)
);
GO

-- ======================================================================
-- 4. TABLAS DE AUDITORÍA (Requisito 4.1.6)
-- ======================================================================

-- AUDITORÍA GENERAL DE VENTAS (JSON texto)
CREATE TABLE dbo.Auditoria_Ventas (
    audit_id        INT IDENTITY(1,1) PRIMARY KEY,
    accion          VARCHAR(10) NOT NULL,  -- INSERT / UPDATE / DELETE
    venta_id        INT,
    usuario         VARCHAR(100),
    fecha_evento    DATETIME      DEFAULT GETDATE(),
    datos_anteriores NVARCHAR(MAX),
    datos_nuevos     NVARCHAR(MAX)
);

-- AUDITORÍA DETALLADA VENTAS
CREATE TABLE dbo.Auditoria_Ventas_Insercion (
    audit_id        INT IDENTITY(1,1) PRIMARY KEY,
    venta_id        INT NOT NULL,
    cliente_id      INT NOT NULL,
    empleado_id     INT NOT NULL,
    fecha_venta     DATETIME,
    total_venta     DECIMAL(18,2),
    metodo_pago     VARCHAR(50),
    estado_venta    VARCHAR(20),
    usuario         VARCHAR(100),
    fecha_insercion DATETIME      DEFAULT GETDATE()
);

CREATE TABLE dbo.Auditoria_Ventas_Actualizacion (
    audit_id               INT IDENTITY(1,1) PRIMARY KEY,
    venta_id               INT NOT NULL,
    cliente_id_anterior    INT,
    empleado_id_anterior   INT,
    fecha_venta_anterior   DATETIME,
    total_venta_anterior   DECIMAL(18,2),
    metodo_pago_anterior   VARCHAR(50),
    estado_venta_anterior  VARCHAR(20),
    cliente_id_nuevo       INT,
    empleado_id_nuevo      INT,
    fecha_venta_nueva      DATETIME,
    total_venta_nueva      DECIMAL(18,2),
    metodo_pago_nuevo      VARCHAR(50),
    estado_venta_nuevo     VARCHAR(20),
    usuario                VARCHAR(100),
    fecha_actualizacion    DATETIME      DEFAULT GETDATE()
);

CREATE TABLE dbo.Auditoria_Ventas_Eliminacion (
    audit_id        INT IDENTITY(1,1) PRIMARY KEY,
    venta_id        INT NOT NULL,
    cliente_id      INT NOT NULL,
    empleado_id     INT NOT NULL,
    fecha_venta     DATETIME,
    total_venta     DECIMAL(18,2),
    metodo_pago     VARCHAR(50),
    estado_venta    VARCHAR(20),
    usuario         VARCHAR(100),
    fecha_eliminacion DATETIME    DEFAULT GETDATE()
);

-- AUDITORÍA GENERAL DE VEHÍCULOS (JSON texto)
CREATE TABLE dbo.Auditoria_Vehiculos (
    audit_id        INT IDENTITY(1,1) PRIMARY KEY,
    accion          VARCHAR(10) NOT NULL,
    vehiculo_id     INT,
    usuario         VARCHAR(100),
    fecha_evento    DATETIME      DEFAULT GETDATE(),
    datos_anteriores NVARCHAR(MAX),
    datos_nuevos     NVARCHAR(MAX)
);

-- AUDITORÍA DETALLADA VEHÍCULOS
CREATE TABLE dbo.Auditoria_Vehiculos_Insercion (
    audit_id               INT IDENTITY(1,1) PRIMARY KEY,
    vehiculo_id            INT NOT NULL,
    marca                  VARCHAR(50),
    modelo                 VARCHAR(50),
    anio                   INT,
    precio                 DECIMAL(18,2),
    color                  VARCHAR(30),
    tipo                   VARCHAR(30),
    estado_disponibilidad  VARCHAR(20),
    usuario                VARCHAR(100),
    fecha_insercion        DATETIME      DEFAULT GETDATE()
);

CREATE TABLE dbo.Auditoria_Vehiculos_Actualizacion (
    audit_id                        INT IDENTITY(1,1) PRIMARY KEY,
    vehiculo_id                     INT NOT NULL,
    marca_anterior                  VARCHAR(50),
    modelo_anterior                 VARCHAR(50),
    anio_anterior                   INT,
    precio_anterior                 DECIMAL(18,2),
    color_anterior                  VARCHAR(30),
    tipo_anterior                   VARCHAR(30),
    estado_disponibilidad_anterior  VARCHAR(20),
    marca_nueva                     VARCHAR(50),
    modelo_nueva                    VARCHAR(50),
    anio_nueva                      INT,
    precio_nueva                    DECIMAL(18,2),
    color_nueva                     VARCHAR(30),
    tipo_nueva                      VARCHAR(30),
    estado_disponibilidad_nueva     VARCHAR(20),
    usuario                         VARCHAR(100),
    fecha_actualizacion             DATETIME      DEFAULT GETDATE()
);

CREATE TABLE dbo.Auditoria_Vehiculos_Eliminacion (
    audit_id               INT IDENTITY(1,1) PRIMARY KEY,
    vehiculo_id            INT NOT NULL,
    marca                  VARCHAR(50),
    modelo                 VARCHAR(50),
    anio                   INT,
    precio                 DECIMAL(18,2),
    color                  VARCHAR(30),
    tipo                   VARCHAR(30),
    estado_disponibilidad  VARCHAR(20),
    usuario                VARCHAR(100),
    fecha_eliminacion      DATETIME      DEFAULT GETDATE()
);

-- AUDITORÍA ERRORES GENERALES
CREATE TABLE dbo.Auditoria_Errores (
    error_id      INT IDENTITY(1,1) PRIMARY KEY,
    procedimiento VARCHAR(100),
    mensaje_error NVARCHAR(4000),
    numero_error  INT,
    usuario       VARCHAR(100),
    fecha_error   DATETIME      DEFAULT GETDATE()
);
GO

-- ======================================================================
-- 5. ÍNDICES (Requisito 7)
-- ======================================================================
CREATE UNIQUE INDEX IX_Clientes_Email          ON dbo.Clientes(email);
CREATE UNIQUE INDEX IX_Clientes_Documento      ON dbo.Clientes(tipo_documento, numero_documento);
CREATE INDEX IX_Vehiculos_Marca_Modelo         ON dbo.Vehiculos(marca, modelo);
CREATE INDEX IX_Vehiculos_Estado               ON dbo.Vehiculos(estado_disponibilidad);
CREATE INDEX IX_Vehiculos_Precio               ON dbo.Vehiculos(precio);
CREATE INDEX IX_Ventas_Fecha                   ON dbo.Ventas(fecha_venta);
CREATE INDEX IX_Ventas_Estado                  ON dbo.Ventas(estado_venta);
CREATE INDEX IX_Ventas_Cliente                 ON dbo.Ventas(cliente_id);
CREATE INDEX IX_Auditoria_Ventas_Fecha         ON dbo.Auditoria_Ventas(fecha_evento);
CREATE INDEX IX_Auditoria_Vehiculos_Fecha      ON dbo.Auditoria_Vehiculos(fecha_evento);
CREATE INDEX IX_Ventas_Cliente_Fecha           ON dbo.Ventas(cliente_id, fecha_venta DESC);
CREATE INDEX IX_Vehiculos_Tipo_Precio          ON dbo.Vehiculos(tipo, precio);
CREATE INDEX IX_Auditoria_VentasIns_Fecha      ON dbo.Auditoria_Ventas_Insercion(fecha_insercion);
CREATE INDEX IX_Auditoria_VentasAct_Fecha      ON dbo.Auditoria_Ventas_Actualizacion(fecha_actualizacion);
CREATE INDEX IX_Auditoria_VentasDel_Fecha      ON dbo.Auditoria_Ventas_Eliminacion(fecha_eliminacion);
GO

-- ======================================================================
-- 6. TRIGGERS (Requisito 1)
-- ======================================================================

-- 6.1 Validación de disponibilidad del vehículo (soporta múltiples filas)
CREATE OR ALTER TRIGGER dbo.trg_ValidarDisponibilidadVehiculo
ON dbo.Detalle_Ventas
INSTEAD OF INSERT
AS
BEGIN
    SET NOCOUNT ON;

    -- Si algún vehículo NO está disponible, rechazar toda la inserción
    IF EXISTS (
        SELECT 1
        FROM inserted i
        JOIN dbo.Vehiculos v ON v.vehiculo_id = i.vehiculo_id
        WHERE v.estado_disponibilidad <> 'Disponible'
    )
    BEGIN
        RAISERROR('Error: Alguno de los vehículos no está disponible para la venta.', 16, 1);
        RETURN;
    END;

    -- Si todos están disponibles, realizar la inserción real
    INSERT INTO dbo.Detalle_Ventas (venta_id, vehiculo_id, precio_unitario, cantidad)
    SELECT i.venta_id, i.vehiculo_id, i.precio_unitario, i.cantidad
    FROM inserted i;
END;
GO

-- 6.2 Auditoría Ventas - Inserciones
CREATE OR ALTER TRIGGER dbo.trg_Auditoria_Ventas_Insercion
ON dbo.Ventas
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO dbo.Auditoria_Ventas_Insercion
        (venta_id, cliente_id, empleado_id, fecha_venta, total_venta, metodo_pago, estado_venta, usuario)
    SELECT 
        i.venta_id, i.cliente_id, i.empleado_id, i.fecha_venta,
        i.total_venta, i.metodo_pago, i.estado_venta, SYSTEM_USER
    FROM inserted i;

    -- Auditoría general JSON (opcional)
    INSERT INTO dbo.Auditoria_Ventas (accion, venta_id, usuario, datos_anteriores, datos_nuevos)
    SELECT
        'INSERT',
        i.venta_id,
        SYSTEM_USER,
        NULL,
        (SELECT i.* FOR JSON PATH, WITHOUT_ARRAY_WRAPPER)
    FROM inserted i;
END;
GO

-- 6.3 Auditoría Ventas - Actualizaciones
CREATE OR ALTER TRIGGER dbo.trg_Auditoria_Ventas_Actualizacion
ON dbo.Ventas
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO dbo.Auditoria_Ventas_Actualizacion
        (venta_id,
         cliente_id_anterior, empleado_id_anterior, fecha_venta_anterior,
         total_venta_anterior, metodo_pago_anterior, estado_venta_anterior,
         cliente_id_nuevo, empleado_id_nuevo, fecha_venta_nueva,
         total_venta_nueva, metodo_pago_nuevo, estado_venta_nuevo,
         usuario)
    SELECT
        i.venta_id,
        d.cliente_id, d.empleado_id, d.fecha_venta,
        d.total_venta, d.metodo_pago, d.estado_venta,
        i.cliente_id, i.empleado_id, i.fecha_venta,
        i.total_venta, i.metodo_pago, i.estado_venta,
        SYSTEM_USER
    FROM inserted i
    INNER JOIN deleted d ON i.venta_id = d.venta_id;

    INSERT INTO dbo.Auditoria_Ventas (accion, venta_id, usuario, datos_anteriores, datos_nuevos)
    SELECT
        'UPDATE',
        i.venta_id,
        SYSTEM_USER,
        (SELECT d.* FOR JSON PATH, WITHOUT_ARRAY_WRAPPER),
        (SELECT i.* FOR JSON PATH, WITHOUT_ARRAY_WRAPPER)
    FROM inserted i
    JOIN deleted d ON i.venta_id = d.venta_id;
END;
GO

-- 6.4 Auditoría Ventas - Eliminaciones
CREATE OR ALTER TRIGGER dbo.trg_Auditoria_Ventas_Eliminacion
ON dbo.Ventas
AFTER DELETE
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO dbo.Auditoria_Ventas_Eliminacion
        (venta_id, cliente_id, empleado_id, fecha_venta, total_venta,
         metodo_pago, estado_venta, usuario)
    SELECT
        d.venta_id, d.cliente_id, d.empleado_id, d.fecha_venta,
        d.total_venta, d.metodo_pago, d.estado_venta, SYSTEM_USER
    FROM deleted d;

    INSERT INTO dbo.Auditoria_Ventas (accion, venta_id, usuario, datos_anteriores, datos_nuevos)
    SELECT
        'DELETE',
        d.venta_id,
        SYSTEM_USER,
        (SELECT d.* FOR JSON PATH, WITHOUT_ARRAY_WRAPPER),
        NULL
    FROM deleted d;
END;
GO

-- 6.5 Auditoría Vehículos - Inserciones
CREATE OR ALTER TRIGGER dbo.trg_Auditoria_Vehiculos_Insercion
ON dbo.Vehiculos
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO dbo.Auditoria_Vehiculos_Insercion
        (vehiculo_id, marca, modelo, anio, precio, color, tipo,
         estado_disponibilidad, usuario)
    SELECT
        i.vehiculo_id, i.marca, i.modelo, i.anio, i.precio, i.color,
        i.tipo, i.estado_disponibilidad, SYSTEM_USER
    FROM inserted i;

    INSERT INTO dbo.Auditoria_Vehiculos (accion, vehiculo_id, usuario, datos_anteriores, datos_nuevos)
    SELECT
        'INSERT',
        i.vehiculo_id,
        SYSTEM_USER,
        NULL,
        (SELECT i.* FOR JSON PATH, WITHOUT_ARRAY_WRAPPER)
    FROM inserted i;
END;
GO

-- 6.6 Auditoría Vehículos - Actualizaciones
CREATE OR ALTER TRIGGER dbo.trg_Auditoria_Vehiculos_Actualizacion
ON dbo.Vehiculos
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO dbo.Auditoria_Vehiculos_Actualizacion
        (vehiculo_id,
         marca_anterior, modelo_anterior, anio_anterior, precio_anterior,
         color_anterior, tipo_anterior, estado_disponibilidad_anterior,
         marca_nueva, modelo_nueva, anio_nueva, precio_nueva,
         color_nueva, tipo_nueva, estado_disponibilidad_nueva,
         usuario)
    SELECT
        i.vehiculo_id,
        d.marca, d.modelo, d.anio, d.precio,
        d.color, d.tipo, d.estado_disponibilidad,
        i.marca, i.modelo, i.anio, i.precio,
        i.color, i.tipo, i.estado_disponibilidad,
        SYSTEM_USER
    FROM inserted i
    JOIN deleted d ON i.vehiculo_id = d.vehiculo_id;

    INSERT INTO dbo.Auditoria_Vehiculos (accion, vehiculo_id, usuario, datos_anteriores, datos_nuevos)
    SELECT
        'UPDATE',
        i.vehiculo_id,
        SYSTEM_USER,
        (SELECT d.* FOR JSON PATH, WITHOUT_ARRAY_WRAPPER),
        (SELECT i.* FOR JSON PATH, WITHOUT_ARRAY_WRAPPER)
    FROM inserted i
    JOIN deleted d ON i.vehiculo_id = d.vehiculo_id;
END;
GO

-- 6.7 Auditoría Vehículos - Eliminaciones
CREATE OR ALTER TRIGGER dbo.trg_Auditoria_Vehiculos_Eliminacion
ON dbo.Vehiculos
AFTER DELETE
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO dbo.Auditoria_Vehiculos_Eliminacion
        (vehiculo_id, marca, modelo, anio, precio,
         color, tipo, estado_disponibilidad, usuario)
    SELECT
        d.vehiculo_id, d.marca, d.modelo, d.anio, d.precio,
        d.color, d.tipo, d.estado_disponibilidad, SYSTEM_USER
    FROM deleted d;

    INSERT INTO dbo.Auditoria_Vehiculos (accion, vehiculo_id, usuario, datos_anteriores, datos_nuevos)
    SELECT
        'DELETE',
        d.vehiculo_id,
        SYSTEM_USER,
        (SELECT d.* FOR JSON PATH, WITHOUT_ARRAY_WRAPPER),
        NULL
    FROM deleted d;
END;
GO

-- ======================================================================
-- 7. PROCEDIMIENTOS ALMACENADOS (Requisito 3 y 8)
-- ======================================================================

-- 7.1 Registrar Venta
CREATE OR ALTER PROCEDURE dbo.sp_RegistrarVenta
    @cliente_id  INT,
    @empleado_id INT,
    @vehiculo_id INT,
    @metodo_pago VARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @precio          DECIMAL(18,2);
    DECLARE @estado          VARCHAR(20);
    DECLARE @nueva_venta_id  INT;
    DECLARE @nombre_vehiculo VARCHAR(100);

    BEGIN TRY
        BEGIN TRANSACTION;

        -- Validaciones
        IF NOT EXISTS (SELECT 1 FROM dbo.Clientes  WHERE cliente_id = @cliente_id  AND activo = 1)
            THROW 50002, 'Cliente no existe o está inactivo.', 1;

        IF NOT EXISTS (SELECT 1 FROM dbo.Empleados WHERE empleado_id = @empleado_id AND activo = 1)
            THROW 50003, 'Empleado no existe o está inactivo.', 1;

        SELECT 
            @precio = precio,
            @estado = estado_disponibilidad,
            @nombre_vehiculo = marca + ' ' + modelo
        FROM dbo.Vehiculos
        WHERE vehiculo_id = @vehiculo_id;

        IF @precio IS NULL
            THROW 50004, 'Vehículo no encontrado.', 1;

        IF @estado <> 'Disponible'
            THROW 50005, 'El vehículo no está disponible para la venta.', 1;

        -- Insertar venta
        INSERT INTO dbo.Ventas (cliente_id, empleado_id, total_venta, metodo_pago)
        VALUES (@cliente_id, @empleado_id, @precio, @metodo_pago);

        SET @nueva_venta_id = SCOPE_IDENTITY();

        -- Insertar detalle (pasa por trg_ValidarDisponibilidadVehiculo)
        INSERT INTO dbo.Detalle_Ventas (venta_id, vehiculo_id, precio_unitario, cantidad)
        VALUES (@nueva_venta_id, @vehiculo_id, @precio, 1);

        -- Actualizar estado del vehículo
        UPDATE dbo.Vehiculos
        SET estado_disponibilidad = 'Vendido'
        WHERE vehiculo_id = @vehiculo_id;

        -- Auditoría de inserción de venta ya la cubre el trigger

        COMMIT TRANSACTION;

        SELECT
            'Éxito'            AS resultado,
            @nueva_venta_id    AS venta_id,
            'Venta registrada correctamente para ' + @nombre_vehiculo AS mensaje;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        INSERT INTO dbo.Auditoria_Errores (procedimiento, mensaje_error, numero_error, usuario)
        VALUES ('sp_RegistrarVenta', ERROR_MESSAGE(), ERROR_NUMBER(), SYSTEM_USER);

        THROW;
    END CATCH
END;
GO

-- 7.2 Cancelar Venta
CREATE OR ALTER PROCEDURE dbo.sp_CancelarVenta
    @venta_id INT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @estado_actual   VARCHAR(20);
    DECLARE @vehiculo_id     INT;
    DECLARE @nombre_vehiculo VARCHAR(100);

    BEGIN TRY
        BEGIN TRANSACTION;

        SELECT @estado_actual = estado_venta
        FROM dbo.Ventas
        WHERE venta_id = @venta_id;

        IF @estado_actual IS NULL
            THROW 50006, 'Venta no encontrada.', 1;

        IF @estado_actual <> 'Activa'
            THROW 50007, 'Solo se pueden cancelar ventas activas.', 1;

        -- Obtener vehículo asociado
        SELECT 
            @vehiculo_id = dv.vehiculo_id,
            @nombre_vehiculo = v.marca + ' ' + v.modelo
        FROM dbo.Detalle_Ventas dv
        JOIN dbo.Vehiculos v ON dv.vehiculo_id = v.vehiculo_id
        WHERE dv.venta_id = @venta_id;

        -- Auditoría antes de cambiar estado (tabla detallada)
        INSERT INTO dbo.Auditoria_Ventas_Actualizacion
            (venta_id,
             cliente_id_anterior, empleado_id_anterior, fecha_venta_anterior,
             total_venta_anterior, metodo_pago_anterior, estado_venta_anterior,
             cliente_id_nuevo, empleado_id_nuevo, fecha_venta_nueva,
             total_venta_nueva, metodo_pago_nuevo, estado_venta_nuevo,
             usuario)
        SELECT
            v.venta_id,
            v.cliente_id, v.empleado_id, v.fecha_venta,
            v.total_venta, v.metodo_pago, v.estado_venta,
            v.cliente_id, v.empleado_id, v.fecha_venta,
            v.total_venta, v.metodo_pago, 'Cancelada',
            SYSTEM_USER
        FROM dbo.Ventas v
        WHERE v.venta_id = @venta_id;

        -- Cancelar venta
        UPDATE dbo.Ventas
        SET estado_venta = 'Cancelada'
        WHERE venta_id = @venta_id;

        -- Devolver vehículo a disponible
        UPDATE dbo.Vehiculos
        SET estado_disponibilidad = 'Disponible'
        WHERE vehiculo_id = @vehiculo_id;

        COMMIT TRANSACTION;

        SELECT
            'Éxito' AS resultado,
            'Venta #' + CAST(@venta_id AS VARCHAR(20)) + 
            ' cancelada. Vehículo ' + @nombre_vehiculo + ' disponible nuevamente.' AS mensaje;
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

-- 7.3 Historial de compras de un cliente
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
        e.nombre_completo AS vendedor
    FROM dbo.Ventas v
    JOIN dbo.Detalle_Ventas dv ON v.venta_id = dv.venta_id
    JOIN dbo.Vehiculos ve      ON dv.vehiculo_id = ve.vehiculo_id
    JOIN dbo.Empleados e       ON v.empleado_id = e.empleado_id
    WHERE v.cliente_id = @cliente_id
    ORDER BY v.fecha_venta DESC;
END;
GO

select * from Empleados
select * from Clientes

-- ======================================================================
-- 8. DATOS INICIALES
-- ======================================================================
INSERT INTO dbo.Empleados (nombre_completo, email, puesto, password_hash, es_administrador)
VALUES
('Administrador Principal', 'admin@rusteze.com', 'Gerente', 'hashed_password_123', 1),
('Vendedor Ejemplo',       'vendedor@rusteze.com', 'Vendedor', 'hashed_password_123', 0);

INSERT INTO dbo.Clientes (nombre_completo, email, telefono, tipo_documento, numero_documento, password_hash)
VALUES
('Cliente Demo', 'cliente@ejemplo.com', '555-1234', 'INE', 'ABC123456', 'hashed_password_123');

INSERT INTO dbo.Vehiculos (marca, modelo, anio, precio, color, tipo, descripcion, imagen_url)
VALUES
('Toyota', 'Corolla', 2024,  450000.00,  'Blanco', 'Sedan',
 'Automóvil familiar confiable y eficiente', '/static/images/vehicles/corolla.jpg'),
('Honda',  'CR-V',    2023,  620000.00,  'Plata',  'SUV',
 'SUV espaciosa y versátil para la familia', '/static/images/vehicles/crv.jpg'),
('Ford',   'Mustang', 2023, 1100000.00,  'Rojo',   'Deportivo',
 'Leyenda americana con potencia y estilo',  '/static/images/vehicles/mustang.jpg');
GO

-- ======================================================================
-- 9. PRUEBAS FUNCIONALES BÁSICAS
-- ======================================================================
PRINT '=== INICIANDO PRUEBAS FUNCIONALES ===';

-- Prueba 1: Venta exitosa
BEGIN TRY
    EXEC dbo.sp_RegistrarVenta 
        @cliente_id = 1, 
        @empleado_id = 2, 
        @vehiculo_id = 1, 
        @metodo_pago = 'Tarjeta';
    PRINT '✓ Prueba 1 PASADA: Venta registrada exitosamente';
END TRY
BEGIN CATCH
    PRINT '✗ Prueba 1 FALLADA: ' + ERROR_MESSAGE();
END CATCH;

-- Prueba 2: Intentar vender vehículo ya vendido (debe fallar)
BEGIN TRY
    EXEC dbo.sp_RegistrarVenta 
        @cliente_id = 1, 
        @empleado_id = 2, 
        @vehiculo_id = 1, 
        @metodo_pago = 'Efectivo';
    PRINT '✗ Prueba 2 FALLADA: Debió generar error por vehículo no disponible';
END TRY
BEGIN CATCH
    PRINT '✓ Prueba 2 PASADA: Correctamente evitó vender vehículo no disponible';
END CATCH;

-- Prueba 3: Cancelar venta
BEGIN TRY
    EXEC dbo.sp_CancelarVenta @venta_id = 1;
    PRINT '✓ Prueba 3 PASADA: Venta cancelada exitosamente';
END TRY
BEGIN CATCH
    PRINT '✗ Prueba 3 FALLADA: ' + ERROR_MESSAGE();
END CATCH;

PRINT '=== PRUEBAS COMPLETADAS ===';
GO

-- Verificación rápida
SELECT name FROM sys.databases WHERE name = 'RustEze_Agency';
GO

USE RustEze_Agency;
GO

SELECT name AS Procedimiento, create_date, modify_date
FROM sys.procedures
WHERE name IN ('sp_RegistrarVenta', 'sp_CancelarVenta', 'sp_HistorialComprasCliente')
ORDER BY name;
GO

SELECT t.name AS TriggerName, OBJECT_NAME(t.parent_id) AS Tabla, t.create_date
FROM sys.triggers t
WHERE t.is_ms_shipped = 0
ORDER BY t.name;
GO

SELECT * FROM Clientes;
SELECT * FROM Vehiculos;
SELECT * FROM Ventas;
GO


SELECT 
    v.vehiculo_id,
    v.marca,
    v.modelo,
    dv.detalle_id,
    dv.venta_id,
    ve.fecha_venta,
    ve.estado_venta,
    ve.total_venta
FROM dbo.Vehiculos v
JOIN dbo.Detalle_Ventas dv ON dv.vehiculo_id = v.vehiculo_id
JOIN dbo.Ventas ve         ON ve.venta_id = dv.venta_id
WHERE v.vehiculo_id = 3;  -- cambia 3 por el ID que quieres borrar







USE RustEze_Agency;
GO

CREATE OR ALTER PROCEDURE dbo.sp_AdminEliminarVehiculo
    @vehiculo_id INT
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        -- 1) Verificar si el vehículo tiene ventas ACTIVAS o FINALIZADAS
        IF EXISTS (
            SELECT 1
            FROM dbo.Detalle_Ventas dv
            JOIN dbo.Ventas ve ON ve.venta_id = dv.venta_id
            WHERE dv.vehiculo_id = @vehiculo_id
              AND ve.estado_venta <> 'Cancelada'
        )
        BEGIN
            THROW 60001, 'No se puede eliminar el vehículo porque tiene ventas activas o finalizadas.', 1;
        END

        -- 2) Eliminar primero los Detalle_Ventas del vehículo
        DELETE dv
        FROM dbo.Detalle_Ventas dv
        WHERE dv.vehiculo_id = @vehiculo_id;

        -- 3) Eliminar las Ventas que se quedaron sin detalle (todas son Canceladas)
        DELETE ve
        FROM dbo.Ventas ve
        WHERE ve.estado_venta = 'Cancelada'
          AND NOT EXISTS (
                SELECT 1
                FROM dbo.Detalle_Ventas dv
                WHERE dv.venta_id = ve.venta_id
          );

        -- 4) Eliminar finalmente el vehículo
        DELETE FROM dbo.Vehiculos
        WHERE vehiculo_id = @vehiculo_id;

        COMMIT TRANSACTION;

        SELECT 
            'Éxito' AS resultado,
            'Vehículo eliminado correctamente.' AS mensaje;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        INSERT INTO dbo.Auditoria_Errores (procedimiento, mensaje_error, numero_error, usuario)
        VALUES ('sp_AdminEliminarVehiculo', ERROR_MESSAGE(), ERROR_NUMBER(), SYSTEM_USER);

        THROW;
    END CATCH
END;
GO


USE RustEze_Agency;
GO

-- 1) Eliminar la FK anterior
ALTER TABLE dbo.Detalle_Ventas
DROP CONSTRAINT FK_Detalle_Vehiculos;
GO

-- 2) Crear la FK con ON DELETE CASCADE
ALTER TABLE dbo.Detalle_Ventas
ADD CONSTRAINT FK_Detalle_Vehiculos
    FOREIGN KEY (vehiculo_id)
    REFERENCES dbo.Vehiculos(vehiculo_id)
    ON DELETE CASCADE;
GO


USE RustEze_Agency;
GO

CREATE OR ALTER PROCEDURE dbo.sp_AdminEliminarVehiculo
    @vehiculo_id INT
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        -- 1) Verificar si el vehículo tiene ventas ACTIVAS o FINALIZADAS
        IF EXISTS (
            SELECT 1
            FROM dbo.Detalle_Ventas dv
            JOIN dbo.Ventas ve ON ve.venta_id = dv.venta_id
            WHERE dv.vehiculo_id = @vehiculo_id
              AND ve.estado_venta <> 'Cancelada'
        )
        BEGIN
            THROW 60001, 'No se puede eliminar el vehículo porque tiene ventas activas o finalizadas.', 1;
        END

        -- 2) Eliminar explícitamente los detalles de ventas de ese vehículo
        DELETE dv
        FROM dbo.Detalle_Ventas dv
        WHERE dv.vehiculo_id = @vehiculo_id;

        -- 3) Eliminar ventas canceladas que se hayan quedado sin detalle
        DELETE ve
        FROM dbo.Ventas ve
        WHERE ve.estado_venta = 'Cancelada'
          AND NOT EXISTS (
                SELECT 1
                FROM dbo.Detalle_Ventas dv
                WHERE dv.venta_id = ve.venta_id
          );

        -- 4) Eliminar el vehículo (si queda, por seguridad)
        DELETE FROM dbo.Vehiculos
        WHERE vehiculo_id = @vehiculo_id;

        COMMIT TRANSACTION;

        SELECT
            'Éxito'  AS resultado,
            'Vehículo eliminado correctamente.' AS mensaje;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        INSERT INTO dbo.Auditoria_Errores (procedimiento, mensaje_error, numero_error, usuario)
        VALUES ('sp_AdminEliminarVehiculo', ERROR_MESSAGE(), ERROR_NUMBER(), SYSTEM_USER);

        THROW;
    END CATCH
END;
GO

EXEC dbo.sp_AdminEliminarVehiculo @vehiculo_id = 3;
