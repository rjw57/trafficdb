import logging

from mixer.backend.flask import mixer

from trafficdb.models import *

from .fixtures import (
    create_fake_observations, create_fake_links,
    create_fake_link_aliases
)
from .util import TestCase, raises_integrity_error

log = logging.getLogger(__name__)

class TestLinksModel(TestCase):
    @classmethod
    def create_fixtures(cls):
        # Create some random links
        link_fixtures = mixer.cycle(5).blend(Link, geom='SRID=4326; LINESTRING EMPTY')
        db.session.add_all(link_fixtures)

    def test_links_created(self):
        link_count = db.session.query(Link).count()
        log.info('Links in database: {0}'.format(link_count))
        assert link_count == 5

class TestRealisticData(TestCase):
    @classmethod
    def create_fixtures(cls):
        create_fake_observations()

    def setUp(self):
        super(TestRealisticData, self).setUp()

        # Extract link ids
        self.link_ids = set(l.id for l in db.session.query(Link.id))

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
        log.info('Observation has link id {0} which should be in {1}'.format(obs.link_id, self.link_ids))
        assert obs is not None
        assert obs.link_id in self.link_ids

        # Try to set it to an invalid link id
        obs.link_id = -1
        db.session.add(obs)
        db.session.commit()

class TestLinkAliases(TestCase):
    @classmethod
    def create_fixtures(cls):
        create_fake_links(link_count=50)
        create_fake_link_aliases(alias_count=30)

    def test_links_created(self):
        link_ids = set(db.session.query(Link.id))
        self.assertEqual(len(link_ids), 50)

    def test_aliases_created(self):
        alias_ids = set(db.session.query(LinkAlias.id))
        self.assertEqual(len(alias_ids), 30)

    def test_aliases_have_link(self):
        n_aliases = 0
        for alias in db.session.query(LinkAlias):
            self.assertIsNotNone(alias.link)
            n_aliases += 1
        self.assertEqual(n_aliases, 30)

    def test_aliases_have_link_via_join(self):
        link_q = db.session.query(LinkAlias.name, Link.uuid).join(Link).order_by(LinkAlias.name)
        n_aliases = 0
        for alias_name, link_uuid in link_q:
            self.assertIsNotNone(alias_name)
            self.assertIsNotNone(link_uuid)
            n_aliases += 1
        self.assertEqual(n_aliases, 30)

