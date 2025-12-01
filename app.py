from flask import Flask, render_template, session, redirect, url_for, flash
from config import Config
from utils.database import init_database
from auth.routes import auth_bp
from admin.routes import admin_bp
from client.routes import client_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializar base de datos
    with app.app_context():
        init_database()
    
    # Registrar blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(client_bp, url_prefix='/client')
    
    # Rutas principales
    @app.route('/')
    def index():
        if 'user_id' in session:
            if session.get('es_administrador'):
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('client.dashboard'))
        return redirect(url_for('auth.login'))
    
    @app.route('/about')
    def about():
        return render_template('about.html', title='Sobre Nosotros')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)