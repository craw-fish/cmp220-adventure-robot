import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config():
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(basedir, 'database', 'adventure_log.db')}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads', 'snapshots')
    DEBUG = False
