import os

from flask.ext.testing import TestCase as FlaskTestCase
from mixer.backend.flask import mixer
from nose.tools import raises
from sqlalchemy import exc

from trafficdb.models import *
from trafficdb.wsgi import app, db

raises_integrity_error = raises(exc.IntegrityError)

class TestCase(FlaskTestCase):
    """flask.ext.testing.TestCase subclass which sets up our mock testing
    database and takes care of clearing it and re-initialising before each
    test.

    Calls create_fixtures() from setUp() to provide an opportunity to create DB
    fixtures.

    """
    def create_app(self):
        # Note that we only every use the SQLALCHEMY_TEST_DATABASE_URI
        # environment variable which means that, hopefully, it would be quite
        # hard to run the test suite against production(!)
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_TEST_DATABASE_URI']
        mixer.init_app(app)
        return app

    def setUp(self):
        # Delete any data initially present
        drop_all_data()

        # Switch on logging
        db.engine.echo = True

        # Create fixtures
        self.create_fixtures()

    def tearDown(self):
        # Switch off logging
        db.engine.echo = False

        db.session.rollback() # If the previous transaction failed
        drop_all_data() # Delete all the data

    def create_fixtures(self):
        pass

def drop_all_data():
    db.session.query(Observation).delete()
    db.session.query(Link).delete()

