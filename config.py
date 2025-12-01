import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'rust-eze-super-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///rusteze.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False