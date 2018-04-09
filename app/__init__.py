from flask import Flask
from flask_login import LoginManager
from flask_pymongo import PyMongo
from flask_bootstrap import Bootstrap
from pymongo import ASCENDING
from config import Config
from threading import Thread

mongo = PyMongo()
login = LoginManager()
login.login_view = 'authentication.login'
login.login_message = 'Please log in to access this page.'
bootstrap = Bootstrap()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    login.init_app(app)
    mongo.init_app(app)
    bootstrap.init_app(app)

    with app.app_context():
        mongo.db.users.create_index([('username', ASCENDING)], unique=True)
        mongo.db.user_requests.create_index([('username', ASCENDING)], unique=True)
        mongo.db.videos.create_index([('title', ASCENDING)], unique=True)
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)
    from app.authentication import bp as authentication_bp
    app.register_blueprint(authentication_bp, url_prefix='/auth')
    from app.videoapp import bp as videoapp_bp
    app.register_blueprint(videoapp_bp)
    Thread(target=video.Video.video_download_procedure, args=(app,)).start()
    return app
from app import usermodel, video

