import logging
import os

from flask import Flask
from flask.ext.migrate import upgrade as db_upgrade, current as db_current
from flask.ext.testing import TestCase
from requests import get

from trafficdb.models import *
from trafficdb.wsgi import app, db

log = logging.getLogger(__name__)

class TestLinksModel(TestCase):
    def create_app(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_TEST_DATABASE_URI']
        return app

    def setUp(self):
        # Delete all links
        db.session.query(Link).delete()

    def test_no_links(self):
        assert db.session.query(Link).count() == 0

class TestObservationModel(TestCase):
    def create_app(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_TEST_DATABASE_URI']
        return app

    def setUp(self):
        # Delete all observations
        db.session.query(Observation).delete()

    def test_no_observations(self):
        assert db.session.query(Observation).count() == 0
