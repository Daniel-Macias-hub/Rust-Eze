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
        nombre = request.form.get("nombre_completo")
        email = request.form.get("email")
        password = request.form.get("password")
        telefono = request.form.get("telefono")

        if not all([nombre, email, password]):
            flash("Por favor completa todos los campos requeridos.", "danger")
            return render_template("auth/register.html")

        try:
            # Para simplificar: se guarda la contraseña en texto plano
            # en la columna password_hash (coincidiendo con tu diseño actual).
            query = """
                INSERT INTO Clientes 
                    (nombre_completo, email, telefono, tipo_documento, 
                     numero_documento, password_hash)
                VALUES (?, ?, ?, 'INE', 'POR_ASIGNAR', ?);
            """
            execute_query(query, (nombre, email, telefono, password), fetch=False)

            flash("Registro exitoso. Por favor inicia sesión.", "success")
            return redirect(url_for("auth.login"))

        except Exception as e:
            flash(f"Error en el registro: {str(e)}", "danger")

    return render_template("auth/register.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión exitosamente.", "info")
    return redirect(url_for("auth.login"))
