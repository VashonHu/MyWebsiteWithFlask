# wsgi.py
# from .app.main import create_app
# from .app import create_app
from app import create_app

application = create_app()

if __name__ == '__main__':
    application.run()
