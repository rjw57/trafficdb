"""
Command-line utility to manage webapp
"""

import logging

from flask.ext.migrate import MigrateCommand
from flask.ext.script import Manager

from .wsgi import app, db, configure_from_environment
from .models import *

log = logging.getLogger(__name__)

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
