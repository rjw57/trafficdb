"""
Command-line utility to manage webapp

"""
from flask.ext.migrate import MigrateCommand
from flask.ext.script import Manager

from .wsgi import create_app

def create_manager():
    # Create app
    app = create_app()

    # Create script manager
    manager = Manager(app)
    manager.add_command('db', MigrateCommand)

    return manager

def main():
    import logging
    logging.basicConfig(level=logging.WARN)
    return create_manager().run()

if __name__ == '__main__':
    main()
