"""
Backend API Configuration
========================
Environment-based configuration for the Training Report Generator API.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration for API service."""
    # Server Configuration
    API_HOST = os.environ.get('API_HOST', '127.0.0.1')
    API_PORT = int(os.environ.get('API_PORT', 5000))
    API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:5000')
    DEBUG_MODE = os.environ.get('DEBUG_MODE', 'False').lower() == 'true'
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'api-dev-key-change-in-production'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16777216))  # 16MB default
    
    # Directory paths
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER') or os.path.join(BASE_DIR, 'output')
    TEMPLATE_FOLDER = os.path.join(BASE_DIR, os.environ.get('TEMPLATES_FOLDER', 'word_templates'))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, os.environ.get('UPLOAD_FOLDER', 'uploads'))
    
    # API Endpoints
    HEALTH_ENDPOINT = os.environ.get('HEALTH_ENDPOINT', '/api/health')
    TEMPLATES_ENDPOINT = os.environ.get('TEMPLATES_ENDPOINT', '/api/templates')
    GENERATE_ENDPOINT = os.environ.get('GENERATE_ENDPOINT', '/api/generate')
    DOWNLOAD_ENDPOINT = os.environ.get('DOWNLOAD_ENDPOINT', '/api/download')
    FILES_LIST_ENDPOINT = os.environ.get('FILES_LIST_ENDPOINT', '/api/files')
    
    # File upload settings
    MAX_FILE_SIZE_MB = int(os.environ.get('MAX_FILE_SIZE_MB', 16))
    ALLOWED_EXTENSIONS = set(os.environ.get('ALLOWED_EXTENSIONS', 'jpg,jpeg,png,gif,bmp,tiff,pdf').split(','))
    UPLOAD_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT_SECONDS', 300))
    
    # Gallery Settings
    MAX_GALLERY_IMAGES = int(os.environ.get('MAX_GALLERY_IMAGES', 10))
    GALLERY_IMAGE_WIDTH_CM = float(os.environ.get('GALLERY_IMAGE_WIDTH_CM', 8.13))
    GALLERY_IMAGE_HEIGHT_CM = float(os.environ.get('GALLERY_IMAGE_HEIGHT_CM', 5.81))
    IMAGES_PER_ROW = int(os.environ.get('IMAGES_PER_ROW', 2))
    IMAGES_PER_PAGE = int(os.environ.get('IMAGES_PER_PAGE', 6))
    
    # Annexure Settings  
    MAX_ANNEXURE_SECTIONS = int(os.environ.get('MAX_ANNEXURE_SECTIONS', 5))
    MAX_IMAGES_PER_ANNEXURE = int(os.environ.get('MAX_IMAGES_PER_ANNEXURE', 10))
    ANNEXURE_IMAGE_WIDTH_CM = float(os.environ.get('ANNEXURE_IMAGE_WIDTH_CM', 15))
    ANNEXURE_IMAGE_HEIGHT_CM = float(os.environ.get('ANNEXURE_IMAGE_HEIGHT_CM', 20))
    
    # Template Configuration
    DEFAULT_TRAINING_TYPE = os.environ.get('DEFAULT_TRAINING_TYPE', 'type_a')
    DEFAULT_TEMPLATE_ID = os.environ.get('DEFAULT_TEMPLATE_ID', '1')
    
    # File Cleanup
    AUTO_CLEANUP_HOURS = int(os.environ.get('AUTO_CLEANUP_HOURS', 24))
    CLEANUP_ON_STARTUP = os.environ.get('CLEANUP_ON_STARTUP', 'True').lower() == 'true'
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',') if os.environ.get('CORS_ORIGINS') else [
        "http://localhost:3000",
        "http://localhost:8000", 
        "http://localhost:8080",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080",
        "https://*.netlify.app",
        "https://*.vercel.app"
    ]
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.environ.get('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    @staticmethod
    def init_app(app):
        """Initialize app with configuration."""
        # Create necessary directories
        os.makedirs(Config.OUTPUT_FOLDER, exist_ok=True)
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(os.path.join(Config.BASE_DIR, 'logs'), exist_ok=True)
        
        # Cleanup old files if enabled
        if Config.CLEANUP_ON_STARTUP:
            from datetime import datetime, timedelta
            import glob
            
            cutoff_time = datetime.now() - timedelta(hours=Config.AUTO_CLEANUP_HOURS)
            
            # Clean output folder
            for file_path in glob.glob(os.path.join(Config.OUTPUT_FOLDER, '*.docx')):
                if os.path.getmtime(file_path) < cutoff_time.timestamp():
                    try:
                        os.remove(file_path)
                        print(f"Cleaned up old file: {os.path.basename(file_path)}")
                    except Exception as e:
                        print(f"Failed to cleanup {file_path}: {e}")

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    ENV = 'development'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    ENV = 'production'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Production logging setup
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug:
            file_handler = RotatingFileHandler(
                'logs/api.log', maxBytes=10240000, backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('API Service startup')

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig, 
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
