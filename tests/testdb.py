import logging

from mixer.backend.flask import mixer

from trafficdb.models import *
from trafficdb.wsgi import db

from .fixtures import create_fake_observations
from .util import TestCase, raises_integrity_error

log = logging.getLogger(__name__)

class TestLinksModel(TestCase):
    def create_fixtures(self):
        # Create some random links
        self.link_fixtures = mixer.cycle(5).blend(Link, geom='SRID=4326; LINESTRING EMPTY')
        db.session.add_all(self.link_fixtures)

    def test_links_created(self):
        link_count = db.session.query(Link).count()
        log.info('Links in database: {0}'.format(link_count))
        assert link_count == 5

class TestRealisticData(TestCase):
    def create_fixtures(self):
        create_fake_observations()

        # Extract link ids
        self.link_ids = set(db.session.query(Link.id))

        # A set of observation times
        self.obs_times = db.session.query(Observation.observed_at).distinct().\
                order_by(Observation.observed_at).all()

    def test_correct_number_created(self):
        for link_id in self.link_ids:
            obs = db.session.query(Observation).filter_by(type=ObservationType.SPEED).\
                    filter_by(link_id=link_id).order_by(Observation.observed_at).all()
            assert len(obs) == len(self.obs_times)

    def test_observations_created(self):
        obs_count = db.session.query(Observation).count()
        log.info('Observations in database: {0}'.format(obs_count))
        assert obs_count > 0

    @raises_integrity_error
    def test_foreign_key_constraint(self):
        # Grab a random observation
        obs = db.session.query(Observation).limit(1).one()
        assert obs is not None
        assert obs.link_id in self.link_ids

        # Try to set it to an invalid link id
        obs.link_id = -1
        db.session.add(obs)
        db.session.commit()
