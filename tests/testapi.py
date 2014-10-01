import datetime
import logging

from sqlalchemy import func
from trafficdb.blueprint.api import PAGE_LIMIT
from trafficdb.models import *

from .fixtures import (
    create_fake_link_aliases,
    create_fake_links,
    create_fake_observations,
)
from .util import ApiTestCase as TestCase, API_PREFIX, strip_url

log = logging.getLogger(__name__)

class TestApiRoot(TestCase):
    def test_api_root(self):
        response = self.client.get(API_PREFIX + '/')
        self.assertIsNot(response.json, None)
        log.info('Got response: {0}'.format(response.json))
        self.assertIn('version', response.json)
        self.assertEquals(response.json['version'], 1)

        resources = response.json['resources']
        self.assertIn('links', resources)
        self.assertIn('linkAliases', resources)

class TestSimpleQueries(TestCase):
    @classmethod
    def create_fixtures(cls):
        start_date = datetime.datetime(2013, 9, 10)

        # NOTE: total links is 104
        create_fake_observations(
            link_count=4, start=start_date, duration=3*24*60)
        create_fake_observations(
            link_count=100, start=start_date, duration=60)

    def test_link_count(self):
        n_links = db.session.query(Link.id).count()
        log.info('Total links: {0}'.format(n_links))
        self.assertEqual(n_links, 104)

    def test_observations_for_non_existant_link(self):
        # Check that non-existent link returns 404
        log.info('Querying for non-existent link')
        response = self.get_observations('X'*22)
        log.info('Got status: {0}'.format(response.status_code))
        self.assertEqual(response.status_code, 404)

    def test_observations_for_bad_link(self):
        # Check that non-existent link whose id is of the wrong format returns 404
        log.info('Querying for non-existent link')
        response = self.get_observations('0')
        log.info('Got status: {0}'.format(response.status_code))
        self.assertEqual(response.status_code, 404)

    def test_observations_for_link_with_negative_duration(self):
        link_id = self.get_some_link_id()
        log.info('Querying for link {0}'.format(link_id))

        response = self.get_observations(link_id, duration=-2)

        # It's a bad request to request a -ve duration
        self.assertEquals(response.status_code, 400)

    def test_observations_for_link_with_bad_duration(self):
        link_id = self.get_some_link_id()
        log.info('Querying for link {0}'.format(link_id))

        response = self.get_observations(link_id, duration='one')

        # It's a bad request to request a non-numeric duration
        self.assertEquals(response.status_code, 400)

    def test_observations_for_link(self):
        link_id = self.get_some_link_id()
        log.info('Querying for link {0}'.format(link_id))

        response = self.get_observations(link_id)
        self.validate_observations_response(link_id, response)

    def test_observations_for_link_at_custom_start(self):
        link_id = self.get_some_link_id()
        log.info('Querying for link {0}'.format(link_id))

        # Get first response
        response = self.get_observations(link_id)
        self.validate_observations_response(link_id, response)

        # Query with start offset
        new_start = response.json['query']['start'] - response.json['query']['duration']
        response = self.get_observations(link_id, start=new_start)
        self.validate_observations_response(link_id, response)
