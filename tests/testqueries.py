import datetime
import logging

import pytz
from trafficdb.models import *
from trafficdb.queries import *

from .fixtures import (
        create_fake_observations,
        create_fake_link_aliases,
        create_fake_links,
)
from .util import TestCase

log = logging.getLogger(__name__)

class TestQueries(TestCase):
    START_DATE = datetime.datetime(2012, 4, 23, tzinfo=pytz.utc)
    END_DATE = datetime.datetime(2012, 4, 25, tzinfo=pytz.utc)

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
        self.assertTrue(len(obs) >= 96)

    def test_multiple_link_observations(self):
        link_ids = db.session.query(Link.id).limit(3).all()
        logging.info('Using link ids: {0}'.format(link_ids))
        obs = observations_for_links(db.session, link_ids, ObservationType.SPEED,
                TestQueries.START_DATE, TestQueries.START_DATE + datetime.timedelta(days=1)).all()
        self.assertTrue(len(obs) >= 96*3)

class TestLinkAlias(TestCase):
    @classmethod
    def create_fixtures(cls):
        create_fake_links(link_count=10)
        create_fake_link_aliases(alias_count=5)

    def test_link_alias_query(self):
        alias_names = list(r[0] for r in \
            db.session.query(LinkAlias.name).order_by(func.random()).limit(2).all())
        alias_names.extend(['_invalid1', '_invalid2'])
        log.info('Resolving aliases: {0}'.format(alias_names))

        q, _ = resolve_link_aliases(db.session, alias_names)
        self.assertEqual(q.count(), len(alias_names))

        for alias, row in zip(alias_names, q):
            log.info('Resolution of {0} is {1}'.format(alias, row))
            self.assertEqual(alias, row[0])
            if alias.startswith('_invalid'):
                self.assertIsNone(row[1])
            else:
                self.assertIsNotNone(row[1])

    def test_multiple_link_alias_query(self):
        # Check that running a query twice does not result in confusion with
        # temporary tables.

        alias_names = list(r[0] for r in \
            db.session.query(LinkAlias.name).order_by(func.random()).limit(2).all())
        alias_names.extend(['_invalid1', '_invalid2'])
        log.info('Resolving aliases: {0}'.format(alias_names))

        q, _ = resolve_link_aliases(db.session, alias_names)
        self.assertEqual(q.count(), len(alias_names))

        for alias, row in zip(alias_names, q):
            log.info('Resolution of {0} is {1}'.format(alias, row))
            self.assertEqual(alias, row[0])
            if alias.startswith('_invalid'):
                self.assertIsNone(row[1])
            else:
                self.assertIsNotNone(row[1])

        q, _ = resolve_link_aliases(db.session, alias_names)
        self.assertEqual(q.count(), len(alias_names))

        for alias, row in zip(alias_names, q):
            log.info('Resolution of {0} is {1}'.format(alias, row))
            self.assertEqual(alias, row[0])
            if alias.startswith('_invalid'):
                self.assertIsNone(row[1])
            else:
                self.assertIsNotNone(row[1])
