# This Python file uses the following encoding: utf-8
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config():
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    FLASK_MAIL_SENDER = u'X乎 <1251562003@qq.com>'
    FLASK_MAIL_ADMIN = '1251562003@qq.com'
    FLASK_FOLLOWERS_PER_PAGE = 20
    FLASK_COMMENTS_PER_PAGE = 20
    FLASK_POSTS_PER_PAGE = 2
    FLASK_ANSWERS_PER_PAGE = 20

    SQLALCHEMY_RECORD_QUERIES = True
    FLASK_DB_QUERY_TIMEOUT = 0.5
    FLASK_SLOW_DB_QUERY_TIME = 0.5

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    MAIL_SERVER = 'smtp.qq.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = '1251562003@qq.com'#os.getenv('MAIL_USERNAME')  #
    MAIL_PASSWORD = 'ahcefwavyfzajfec'#os.getenv('MAIL_PASSWORD')  #
    #SQLALCHEMY_DATABASE_URI = "mysql://root:hu123456@localhost:3306/mywebsite"#'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')#"mysql://root:hu123456@localhost:3306/mywebsite"
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')#"mysql://root:hu123456@localhost:3306/mywebsite"
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')
    SQLALCHEMY_TRACK_MODIFICATIONS = True


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

