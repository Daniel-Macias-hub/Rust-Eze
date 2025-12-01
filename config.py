import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # CONEXIÓN SQL SERVER EXPRESS
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mssql+pyodbc://@localhost\\SQLEXPRESS/RustEze_Agency?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración específica para SQL Server
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'connect_args': {
            'timeout': 30,
            'autocommit': True,
        }
    }
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'rust-eze-super-secret-key-2025'
    
    # Configuración de sesión
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600