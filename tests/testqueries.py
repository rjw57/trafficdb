import datetime
import logging

from trafficdb.models import *
from trafficdb.queries import *
from trafficdb.wsgi import db

from .fixtures import create_fake_observations
from .util import TestCase

log = logging.getLogger(__name__)

class TestQueries(TestCase):
    START_DATE = datetime.datetime(2012, 4, 23)
    END_DATE = datetime.datetime(2012, 4, 25)

    @classmethod
    def create_fixtures(cls):
        duration = int((TestQueries.END_DATE - TestQueries.START_DATE).total_seconds() // 60)
        create_fake_observations(start=TestQueries.START_DATE, duration=duration)

    def test_observations_created(self):
        self.assertNotEqual(db.session.query(Observation.id).count(), 0)

    def test_date_range(self):
        min_d, max_d = observation_date_range(db.session).first()
        log.info('Min and max dates returned: {0} and {1}'.format(min_d, max_d))
        assert min_d >= TestQueries.START_DATE
        assert max_d <= TestQueries.END_DATE
        assert (max_d - min_d).total_seconds() > 60

    def test_single_link_observations(self):
        link_id = db.session.query(Link.id).limit(1).first().id
        logging.info('Fetching observations for link {0}'.format(link_id))
        obs = observations_for_link(db.session, link_id, ObservationType.SPEED,
                TestQueries.START_DATE, TestQueries.START_DATE + datetime.timedelta(days=1)).all()
        self.assertEqual(len(obs), 97)

    def test_multiple_link_observations(self):
        link_ids = db.session.query(Link.id).limit(3).all()
        logging.info('Using link ids: {0}'.format(link_ids))
        obs = observations_for_links(db.session, link_ids, ObservationType.SPEED,
                TestQueries.START_DATE, TestQueries.START_DATE + datetime.timedelta(days=1)).all()
        self.assertEqual(len(obs), 97*3)
