import logging

from mixer.backend.flask import mixer

from trafficdb.models import *
from trafficdb.wsgi import db

from .util import TestCase, raises_integrity_error

log = logging.getLogger(__name__)

API_PREFIX = '/api'

class TestApi(TestCase):
    def test_api_root(self):
        response = self.client.get(API_PREFIX + '/')
        self.assertIsNot(response.json, None)
        self.assertEquals(response.json, dict(version=1))
