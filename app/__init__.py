from flask import Flask
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from config import config
from flask_login import LoginManager
from flask_pagedown import PageDown


bootstrap = Bootstrap()
moment = Moment()
db = SQLAlchemy()
mail = Mail()
log_manager = LoginManager()
log_manager.session_protection = 'strong'
log_manager.login_view = 'auth.aaqqlogin'
pagedown = PageDown()


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    mail.init_app(app)
    log_manager.init_app(app)
    pagedown.init_app(app)

    from .main import main
    app.register_blueprint(main)
    from .auth import auth
    app.register_blueprint(auth, url_prefix='/auth')

    return app

from . import email, models, decorators