import re

# auth/routes.py
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)
from utils.database import execute_query  # Asegúrate de que existe esta función

auth_bp = Blueprint("auth", __name__)  # nombre = 'auth'
def is_strong_password(pwd: str) -> bool:
    """
    Regla:
    - Al menos 8 caracteres
    - Al menos una mayúscula
    - Al menos un número
    - Al menos un carácter especial de !@#$%&*
    """
    if len(pwd) < 8:
        return False
    if not re.search(r"[A-Z]", pwd):
        return False
    if not re.search(r"[0-9]", pwd):
        return False
    if not re.search(r"[!@#$%&*]", pwd):
        return False
    return True

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user_type = request.form.get("user_type")  # 'client' o 'admin'

        if not email or not password or not user_type:
            flash("Por favor completa todos los campos.", "danger")
            return render_template("auth/login.html")

        # =====================================================================
        # AUTENTICACIÓN CONTRA SQL SERVER
        # Para este proyecto se asume que:
        # - En Empleados.password_hash y Clientes.password_hash está guardada
        #   la contraseña tal cual se debe escribir en el login (plaintext),
        #   por ejemplo: 'hashed_password_123'.
        # =====================================================================

        if user_type == "admin":
            query = """
                SELECT 
                    empleado_id AS id,
                    nombre_completo,
                    email,
                    puesto,
                    es_administrador
                FROM Empleados
                WHERE email = ? 
                  AND password_hash = ?
                  AND activo = 1
                  AND es_administrador = 1;
            """
        else:
            query = """
                SELECT 
                    cliente_id AS id,
                    nombre_completo,
                    email
                FROM Clientes
                WHERE email = ?
                  AND password_hash = ?
                  AND activo = 1;
            """

        rows = execute_query(query, (email, password), fetch=True)

        if not rows:
            flash("Credenciales incorrectas o usuario inactivo.", "danger")
            return render_template("auth/login.html")

        # Normalizar el resultado tanto si viene como dict como si viene como tupla
        row = rows[0]

        def get_val(r, idx, key):
            try:
                return r[key]
            except (TypeError, KeyError, AttributeError):
                return r[idx]

        if user_type == "admin":
            user = {
                "id": get_val(row, 0, "id"),
                "nombre_completo": get_val(row, 1, "nombre_completo"),
                "email": get_val(row, 2, "email"),
                "puesto": get_val(row, 3, "puesto"),
            }
        else:
            user = {
                "id": get_val(row, 0, "id"),
                "nombre_completo": get_val(row, 1, "nombre_completo"),
                "email": get_val(row, 2, "email"),
            }

        # =====================================================================
        # SESIÓN
        # =====================================================================
        session.clear()
        session["user_id"] = user["id"]
        session["user_name"] = user["nombre_completo"]
        session["user_email"] = user["email"]
        session["es_administrador"] = user_type == "admin"

        if user_type == "admin":
            session["puesto"] = user.get("puesto", "Administrador")
            flash(f'¡Bienvenido/a {user["nombre_completo"]} (Administrador)!', "success")
            # Debes tener definido el endpoint 'admin.dashboard'
            return redirect(url_for("admin.dashboard"))
        else:
            flash(f'¡Bienvenido/a {user["nombre_completo"]}!', "success")
            # Debes tener definido el endpoint 'client.dashboard'
            return redirect(url_for("client.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nombre = (request.form.get("nombre_completo") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = (request.form.get("password") or "").strip()
        telefono = (request.form.get("telefono") or "").strip()

        # 1) Validaciones básicas
        if not nombre or not email or not password or not telefono:
            flash("Por favor completa todos los campos obligatorios.", "danger")
            return render_template("auth/register.html")

        # 2) Validar contraseña fuerte
        if not is_strong_password(password):
            flash(
                "La contraseña debe tener al menos 8 caracteres, "
                "una letra mayúscula, un número y un carácter especial (!@#$%&*).",
                "danger",
            )
            return render_template("auth/register.html")

        # (Opcional) Validación simple de formato de teléfono
        # Puedes ajustar este regex según tus reglas.
        if not re.fullmatch(r"[0-9+\-\s]{8,20}", telefono):
            flash("El teléfono debe contener solo dígitos y/o símbolos + - con longitud válida.", "danger")
            return render_template("auth/register.html")

        try:
            # 3) Verificar si ya existe el correo
            query_email = "SELECT 1 AS existe FROM Clientes WHERE email = ?;"
            rows_email = execute_query(query_email, (email,), fetch=True)
            if rows_email:
                flash("Ya existe una cuenta registrada con ese correo.", "warning")
                return render_template("auth/register.html")

            # 4) Verificar si ya existe el teléfono
            query_tel = "SELECT 1 AS existe FROM Clientes WHERE telefono = ?;"
            rows_tel = execute_query(query_tel, (telefono,), fetch=True)
            if rows_tel:
                flash("El teléfono ingresado ya está registrado en otra cuenta.", "warning")
                return render_template("auth/register.html")

            # 5) Manejo interno de documento (ya no se pide al usuario)
            #    Cumplimos con NOT NULL + UNIQUE(tipo_documento, numero_documento)
            tipo_documento = "AUTOGEN"
            numero_documento = f"TEL-{telefono}"

            # 6) Insertar nuevo cliente
            #    (Seguimos guardando password en texto plano en password_hash
            #     para no cambiar la lógica de login todavía.)
            insert_query = """
                INSERT INTO Clientes 
                    (nombre_completo, email, telefono, tipo_documento, 
                     numero_documento, password_hash)
                VALUES (?, ?, ?, ?, ?, ?);
            """
            execute_query(
                insert_query,
                (nombre, email, telefono, tipo_documento, numero_documento, password),
                fetch=False,
            )

            # 7) Mostrar pantalla de éxito con animación y luego redirigir a login
            return render_template("auth/register_success.html", nombre=nombre)

        except Exception as e:
            flash(f"Error en el registro: {str(e)}", "danger")

    return render_template("auth/register.html")



@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión exitosamente.", "info")
    return redirect(url_for("auth.login"))
