from flask import Flask, render_template, session, redirect, url_for, flash
from config import Config
from utils.database_sqlserver import init_app as init_database, execute_query
from auth.routes import auth_bp
from admin.routes import admin_bp
from client.routes import client_bp
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializar SQL Server
    init_database(app)
    
    # Registrar blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(client_bp, url_prefix='/client')
    
    # Context processor para funciones globales en templates
    @app.context_processor
    def utility_processor():
        def format_currency(value):
            """Formatear moneda para templates (REQUISITO 6: CASE)"""
            if not value:
                return "$0.00"
            return f"${value:,.2f}"
        
        def get_user_role():
            """Obtener rol del usuario"""
            return 'admin' if session.get('es_administrador') else 'client'
        
        return dict(
            format_currency=format_currency,
            get_user_role=get_user_role
        )
    
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
    
    # Manejo de errores global (REQUISITO 8)
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        # Registrar error en auditoría
        try:
            execute_query("""
                INSERT INTO Auditoria_Errores (procedimiento, mensaje_error, usuario)
                VALUES (?, ?, ?)
            """, ('app.internal_error', str(error), session.get('user_name', 'Anónimo')))
        except:
            pass
        return render_template('errors/500.html'), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Verificar estructura de base de datos
    with app.app_context():
        try:
            # Verificar que las tablas de auditoría existan
            tables = execute_query("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME IN ('Auditoria_Ventas', 'Auditoria_Vehiculos', 'Auditoria_Errores')
            """)
            
            if len(tables) == 3:
                logger.info("✅ Todas las tablas de auditoría presentes")
            else:
                logger.warning("⚠️ Algunas tablas de auditoría faltan")
                logger.warning("   Ejecuta el script BD_Definitiva.txt en SQL Server")
                
        except Exception as e:
            logger.error(f"❌ Error verificando base de datos: {e}")
            logger.error("   Asegúrate de que:")
            logger.error("   1. SQL Server 2022 esté instalado")
            logger.error("   2. El script BD_Definitiva.txt se haya ejecutado")
            logger.error("   3. El servicio SQL Server esté corriendo")
            raise
    
    app.run(debug=True, host='0.0.0.0', port=5000)