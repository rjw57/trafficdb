import datetime
import logging

from trafficdb.models import *
from trafficdb.queries import *
from trafficdb.wsgi import db

from .fixtures import create_fake_observations
from .util import TestCase

log = logging.getLogger(__name__)

class TestQueries(TestCase):
    def create_fixtures(self):
        self.start_date = datetime.datetime(2012, 4, 23)
        self.end_date = datetime.datetime(2012, 4, 25)
        duration = int((self.end_date - self.start_date).total_seconds() // 60)
        create_fake_observations(start=self.start_date, duration=duration)

    def test_observations_created(self):
        self.assertNotEqual(db.session.query(Observation.id).count(), 0)

    def test_single_link_observations(self):
        link_id = db.session.query(Link.id).limit(1).first().id
        logging.info('Fetching observations for link {0}'.format(link_id))
        obs = observations_for_link(db.session, link_id, ObservationType.SPEED,
                self.start_date, self.start_date + datetime.timedelta(days=1)).all()
        self.assertEqual(len(obs), 97)
