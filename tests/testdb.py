import logging
import os

from flask import Flask
from flask.ext.migrate import upgrade as db_upgrade, current as db_current
from flask.ext.testing import TestCase
from mixer.backend.flask import mixer

from trafficdb.models import *
from trafficdb.wsgi import app, db

log = logging.getLogger(__name__)

class TestLinksModel(TestCase):
    def create_app(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_TEST_DATABASE_URI']
        mixer.init_app(app)
        return app

    def setUp(self):
        # Delete all links
        db.session.query(Link).delete()

        # Create some random links
        self.link_fixtures = mixer.cycle(5).blend(Link)

    def test_links_created(self):
        assert db.session.query(Link).count() == 5

class TestObservationModel(TestCase):
    def create_app(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_TEST_DATABASE_URI']
        mixer.init_app(app)
        return app

    def setUp(self):
        # Delete all links and all observations
        db.session.query(Link).delete()
        db.session.query(Observation).delete()

        # Create some random links
        self.link_fixtures = mixer.cycle(5).blend(Link)

        # Create some random observations
        self.observation_fixtures = mixer.cycle(10).blend(Observation,
            link_id=(link.id for link in self.link_fixtures))

    def test_observations_created(self):
        assert db.session.query(Observation).count() == 10
