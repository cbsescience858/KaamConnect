import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'kaamconnect-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Socket.IO Configuration
    SOCKETIO_MESSAGE_QUEUE = os.environ.get('REDIS_URL') or None
    
    # Language Support
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'hi': 'हिंदी',
        'ta': 'தமிழ்',
        'te': 'తెలుగు',
        'kn': 'ಕನ್ನಡ',
        'bn': 'বাংলা',
        'mr': 'मराठी',
        'gu': 'ગુજરાતી'
    }
    
    # Job Categories
    JOB_CATEGORIES = [
        'Software Development',
        'Design',
        'Writing',
        'Translation',
        'Marketing',
        'Business',
        'Education',
        'Healthcare',
        'Manual Labor',
        'Other'
    ]
