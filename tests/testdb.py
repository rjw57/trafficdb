import logging

from flask import Flask
from flask.ext.migrate import upgrade as db_upgrade, current as db_current
from flask.ext.testing import TestCase
from requests import get

from trafficdb.models import *
from trafficdb.wsgi import app, db

log = logging.getLogger(__name__)

# Configure our app to use a new postgression database
app.config['SQLALCHEMY_DATABASE_URI'] = get('http://api.postgression.com').text

class TestMigration(TestCase):
    def create_app(self):
        return app

    def setUp(self):
        # Perform an upgrade to ensure the schema
        db_upgrade()

    def test_current(Self):
        # Should not throw
        db_current()

class TestLinksModel(TestCase):
    def create_app(self):
        return app

    def setUp(self):
        # Perform an upgrade to ensure the schema
        db_upgrade()

        # Delete all links
        db.session.query(Link).delete()

    def test_no_links(self):
        assert db.session.query(Link).count() == 0

class TestObservationModel(TestCase):
    def create_app(self):
        return app

    def setUp(self):
        # Perform an upgrade to ensure the schema
        db_upgrade()

        # Delete all observations
        db.session.query(Observation).delete()

    def test_no_observations(self):
        assert db.session.query(Observation).count() == 0
