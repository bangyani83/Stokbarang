import os
from datetime import datetime

class Config:
    # Secret key untuk session dan security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-fifo-stock-2024-very-secret'
    
    # Database configuration
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'database', 'fifo.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload configuration
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Report configuration
    REPORT_FOLDER = os.path.join(BASE_DIR, 'reports')
    
    # Backup configuration
    BACKUP_FOLDER = os.path.join(BASE_DIR, 'backups')
    
    # Application settings
    APP_NAME = 'FIFO Stock Management'
    APP_VERSION = '1.0.0'
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        # Create necessary directories
        directories = [
            'database',
            'uploads', 
            'reports',
            'backups',
            'app/templates',
            'app/static/css',
            'app/static/js'
        ]
        
        for directory in directories:
            dir_path = os.path.join(app.config['BASE_DIR'], directory)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                print(f"✓ Created directory: {directory}")
