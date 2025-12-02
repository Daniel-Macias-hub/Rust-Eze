from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils.database import User, execute_query

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('user_type')  # 'client' or 'admin'
        
        if not email or not password:
            flash('Por favor ingresa email y contraseña.', 'danger')
            return render_template('auth/login.html')
        
        # Autenticar usuario contra SQL Server
        is_admin = (user_type == 'admin')
        user = User.authenticate(email, password, is_admin)
        
        if user:
            # Configurar sesión
            session['user_id'] = user['id']
            session['user_name'] = user['nombre_completo']
            session['user_email'] = user['email']
            session['es_administrador'] = is_admin
            
            if is_admin:
                session['puesto'] = user.get('puesto', 'Administrador')
                flash(f'¡Bienvenido/a {user["nombre_completo"]}!', 'success')
                return redirect(url_for('admin.dashboard'))
            else:
                flash(f'¡Bienvenido/a {user["nombre_completo"]}!', 'success')
                return redirect(url_for('client.dashboard'))
        else:
            flash('Credenciales incorrectas. Por favor intenta nuevamente.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form.get('nombre_completo')
        email = request.form.get('email')
        password = request.form.get('password')
        telefono = request.form.get('telefono')
        
        if not all([nombre, email, password]):
            flash('Por favor completa todos los campos requeridos.', 'danger')
            return render_template('auth/register.html')
        
        try:
            # Hash password
            hashed_password = User.hash_password(password)
            
            # Insertar nuevo cliente
            query = """
                INSERT INTO Clientes (nombre_completo, email, telefono, tipo_documento, 
                                     numero_documento, password_hash)
                VALUES (?, ?, ?, 'INE', 'POR_ASIGNAR', ?)
            """
            
            execute_query(query, (nombre, email, telefono, hashed_password), fetch=False)
            
            flash('Registro exitoso. Por favor inicia sesión.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            flash(f'Error en el registro: {str(e)}', 'danger')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect(url_for('auth.login'))