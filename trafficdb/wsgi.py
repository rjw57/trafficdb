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

def _default_index(obj, key, default=None):
    try:
        return obj[key]
    except (KeyError, IndexError):
        return default

# Default configuration
class AppConfig(object):
    SQLALCHEMY_DATABASE_URI = _default_index(os.environ, 'SQLALCHEMY_DATABASE_URI')

# Create root webapp
app = Flask(__name__)
app.config.from_object('trafficdb.wsgi.AppConfig')

# Create app database
db = SQLAlchemy(app)

# Create migration helper
migrate = Migrate(app, db)

# Create blueprints
import trafficdb.blueprint as bp
for bp_name in bp.__all__:
    app.register_blueprint(getattr(bp, bp_name), url_prefix='/'+bp_name)
