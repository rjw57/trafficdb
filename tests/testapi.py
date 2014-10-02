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
