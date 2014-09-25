import logging

from flask.ext.migrate import upgrade as db_upgrade, current as db_current
from mixer.backend.flask import mixer

from trafficdb.models import *
from trafficdb.wsgi import db

from .util import TestCase, raises_integrity_error

log = logging.getLogger(__name__)

class TestLinksModel(TestCase):
    def create_fixtures(self):
        # Create some random links
        self.link_fixtures = mixer.cycle(5).blend(Link)

    def test_links_created(self):
        link_count = db.session.query(Link).count()
        log.info('Links in database: {0}'.format(link_count))
        assert link_count == 5

class TestObservationModel(TestCase):
    def create_fixtures(self):
        # Create some random links
        self.link_fixtures = mixer.cycle(5).blend(Link)

        # Create some random observations
        self.observation_fixtures = mixer.cycle(10).blend(Observation,
            link_id=(link.id for link in self.link_fixtures))

    def test_link_attribute(self):
        link_ids = set(link.id for link in db.session.query(Link))
        for o in db.session.query(Observation):
            assert o.link is not None
            assert hasattr(o.link, 'id')
            log.info('Observation {0.id} with link {1.id}'.format(o, o.link))
            assert o.link.id == o.link_id
            assert o.link_id in link_ids

    def test_observations_created(self):
        obs_count = db.session.query(Observation).count()
        log.info('Observations in database: {0}'.format(obs_count))
        assert obs_count == 10

    @raises_integrity_error
    def test_foreign_key_constraint(self):
        db.session.add(Observation(link_id=-1))
        db.session.commit()
