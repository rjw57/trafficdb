"""
WSGI-compatible web application
===============================

This module may also be run-directly via the ``trafficdb_webapp`` script.
"""
import logging
import os

from flask import Flask
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager
from flask.ext.sqlalchemy import SQLAlchemy

log = logging.getLogger(__name__)

# Create root webapp
app = Flask(__name__)

# Create app database
db = SQLAlchemy(app)

# Create migration helper
migrate = Migrate(app, db)

def configure_from_environment():
    # Try to configure sqlite database URI from environment variable
    try:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']
    except KeyError:
        log.warn('SQLALCHEMY_DATABASE_URI environment variable undefined.')
        log.warn('Without it, the app doesn\'t know where to find the database.')

def main():
    # Set up logging
    logging.basicConfig(level=logging.WARN)

    # Attempt to configure app from environment
    configure_from_environment()

    # Create script manager
    manager = Manager(app)
    manager.add_command('db', MigrateCommand)

    return manager.run()

if __name__ == '__main__':
    main()
