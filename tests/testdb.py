import logging
import os

from flask import Flask
from flask.ext.migrate import upgrade as db_upgrade, current as db_current
from flask.ext.testing import TestCase
from mixer.backend.flask import mixer
from nose.tools import raises
from sqlalchemy import exc

from trafficdb.models import *
from trafficdb.wsgi import app, db

log = logging.getLogger(__name__)

def delete_all(session):
    db.session.query(Observation).delete()
    db.session.query(Link).delete()

class TestLinksModel(TestCase):
    def create_app(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_TEST_DATABASE_URI']
        mixer.init_app(app)
        return app

    def setUp(self):
        # Delete any data initially present
        delete_all(db.session)

        # Create some random links
        self.link_fixtures = mixer.cycle(5).blend(Link)

    def tearDown(self):
        # Delete all the data
        self.link_fixtures = None
        db.session.rollback() # If the previous transaction failed
        delete_all(db.session)

    def test_links_created(self):
        link_count = db.session.query(Link).count()
        log.info('Links in database: {0}'.format(link_count))
        assert link_count == 5

class TestObservationModel(TestCase):
    def create_app(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_TEST_DATABASE_URI']
        mixer.init_app(app)
        return app

    def setUp(self):
        delete_all(db.session)

        # Create some random links
        self.link_fixtures = mixer.cycle(5).blend(Link)

        # Create some random observations
        self.observation_fixtures = mixer.cycle(10).blend(Observation,
            link_id=(link.id for link in self.link_fixtures))

    def tearDown(self):
        # Delete all the data
        self.link_fixtures = self.observation_fixtures = None
        db.session.rollback() # If the previous transaction failed
        delete_all(db.session)

    def test_observations_created(self):
        obs_count = db.session.query(Observation).count()
        log.info('Observations in database: {0}'.format(obs_count))
        assert obs_count == 10

    @raises(exc.IntegrityError)
    def test_foreign_key_constraint(self):
        db.session.add(Observation(link_id=-1))
        db.session.commit()
