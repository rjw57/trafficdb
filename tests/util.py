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

# Create our test suite app
log.info('Creating new flask app')
app = create_app()

# Setup mixer
mixer.init_app(app)

class TestCase(FlaskTestCase):
    """flask.ext.testing.TestCase subclass which sets up our mock testing
    database and takes care of clearing it and re-initialising before each
    test.

    Calls classmethod create_fixtures() from setUpClass() to provide an
    opportunity to create DB fixtures.

    """
    def create_app(self):
        return app

    @classmethod
    def setUpClass(cls):
        with app.app_context():
            # Delete any data initially present
            drop_all_data()

            # Create fixtures
            cls.create_fixtures()
            db.session.commit()

    def setUp(self):
        # Switch on logging
        db.engine.echo = True

        # Start transaction
        db.session.begin_nested()

    def tearDown(self):
        db.session.rollback() # If the previous transaction failed

        # Switch off logging
        db.engine.echo = False

    @classmethod
    def create_fixtures(cls):
        pass

def drop_all_data():
    db.session.query(Observation).delete()
    db.session.query(Link).delete()

