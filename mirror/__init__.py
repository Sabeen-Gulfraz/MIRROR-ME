from flask import Flask, url_for
from flask_migrate import Migrate

from .extns import db
from .home import home
from .user import user
from .tailor import tailor
from .courier import courier


def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = "mm123"

    app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root@localhost/mirror_me"

    # BLUEPRINT REGISTRATION
    app.register_blueprint(home)
    app.register_blueprint(user)
    app.register_blueprint(tailor)
    app.register_blueprint(courier)

    db.init_app(app)
    migrate = Migrate(app, db)

    return app
