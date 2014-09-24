import logging

from flask import Flask
from flask.ext.migrate import upgrade as db_upgrade, current as db_current
from flask.ext.testing import TestCase
from requests import get

from trafficdb.wsgi import app, db

log = logging.getLogger(__name__)

# Configure our app to use a new postgression database
app.config['SQLALCHEMY_DATABASE_URI'] = get('http://api.postgression.com').text

class TestMigration(TestCase):
    def create_app(self):
        return app

    def setup(self):
        # Perform an upgrade to ensure the schema
        db_upgrade()

    def test_current(Self):
        # Should not throw
        db_current()
