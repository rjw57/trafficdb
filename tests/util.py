import logging
import os

from flask.ext.testing import TestCase as FlaskTestCase
from mixer.backend.flask import mixer
from nose.tools import raises
from sqlalchemy import exc

from trafficdb.models import *
from trafficdb.wsgi import create_app

log = logging.getLogger(__name__)

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

        # Create our test suite app
        log.info('Creating new flask app')
        app = create_app()
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_TEST_DATABASE_URI']

        # Setup mixer
        mixer.init_app(app)

        with app.app_context():
            # Delete any data initially present
            drop_all_data()

            # Create fixtures
            self.create_fixtures()
            db.session.commit()

        return app

    def setUp(self):
        # Switch on logging
        db.engine.echo = True

        # Start transaction
        db.session.begin_nested()

    def tearDown(self):
        db.session.rollback() # If the previous transaction failed

        # Switch off logging
        db.engine.echo = False

    def create_fixtures(self):
        pass

def drop_all_data():
    db.session.query(Observation).delete()
    db.session.query(Link).delete()

