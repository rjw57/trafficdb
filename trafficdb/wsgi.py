"""
WSGI-compatible web application
===============================

"""
from flask import Flask
from flask.ext.migrate import Migrate

def create_app():
    # Create root webapp
    app = Flask(__name__)
    app.config.from_pyfile('defaultconfig.py')

    # Register this app with the database
    from trafficdb.models import db
    db.init_app(app)

    # Create migration helper
    migrate = Migrate(app, db)

    # Create blueprints
    import trafficdb.blueprint as bp
    for bp_name in bp.__all__:
        app.register_blueprint(getattr(bp, bp_name), url_prefix='/'+bp_name)

    return app
