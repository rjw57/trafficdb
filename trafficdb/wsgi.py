"""
WSGI-compatible web application
===============================

"""
import logging
import os

from flask import Flask
from flask.ext.migrate import Migrate
from flask.ext.sqlalchemy import SQLAlchemy

log = logging.getLogger(__name__)

# Create root webapp
app = Flask(__name__)

# Create app database
db = SQLAlchemy(app)

# Create migration helper
migrate = Migrate(app, db)

# Create blueprints
import trafficdb.blueprint as bp
for bp_name in bp.__all__:
    app.register_blueprint(getattr(bp, bp_name), url_prefix='/'+bp_name)

def configure_from_environment():
    # Try to configure sqlite database URI from environment variable
    try:
        database_uri = os.environ['SQLALCHEMY_DATABASE_URI']
    except KeyError:
        log.warn('SQLALCHEMY_DATABASE_URI environment variable undefined.')
        log.warn('Without it, the app doesn\'t know where to find the database.')
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
