import json
import logging
import os
try:
    from urlparse import urljoin
    from urllib import urlencode
except ImportError:
    from urllib.parse import urljoin, urlencode

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

# Switch on logging for sqlalchemy
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

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

            # Create fixtures with logging temporarily disabled
            cls.create_fixtures()
            db.session.commit()

    def setUp(self):
        # Start transaction
        db.session.begin_nested()

    def tearDown(self):
        db.session.rollback() # If the previous transaction failed

    @classmethod
    def create_fixtures(cls):
        pass

def drop_all_data():
    db.session.query(Observation).delete()
    db.session.query(LinkAlias).delete()
    db.session.query(Link).delete()

API_PREFIX = '/api'

def strip_url(url):
    """Strip leading http://localhost from URLs since our client mock doesn't
    deal with it.

    """
    prefix = 'http://localhost'
    if url.startswith(prefix):
        url = url[len(prefix):]
    return url

class ApiTestCase(TestCase):
    """Specialised test case for API tests with some utility methods.

    """
    def get_page(self, url, from_=None, count=None):
        """Generic function to get a paged URL."""
        query = {}
        if from_ is not None:
            query['from'] = from_
        if count is not None:
            query['count'] = count
        if len(query) > 0:
            url = url + '?' + urlencode(query)
        log.info('GET {0}'.format(url))
        return self.client.get(url)

    def get_links(self, from_=None, count=None):
        """Make a links query"""
        return self.get_page(
            url = API_PREFIX + '/links/',
            from_= from_, count = count,
        )

    def get_some_link_id(self):
        log.info('Querying first link')
        response = self.get_links(count=1)
        properties, page, links = self.parse_links_response(response)
        return links[0]['id']

    def get_observations(self, link_id, start=None, duration=None):
        """Make an observations query"""
        query = {}
        if start is not None:
            query['start'] = start
        if duration is not None:
            query['duration'] = duration
        url = API_PREFIX + '/links/{0}/observations'.format(link_id)
        if len(query) > 0:
            url += '?' + urlencode(query)
        log.info('GET {0}'.format(url))
        return self.client.get(url)

    def get_link_aliases(self, from_=None, count=None):
        """Make a link alias query"""
        return self.get_page(
            url = API_PREFIX + '/aliases/',
            from_= from_, count = count,
        )

    def validate_observations_response(self, link_id, response):
        # Response should look like:
        # {
        #   "link": {
        #       id: <string>,
        #   },
        #   "data": {
        #       <string>: {
        #           "values": <array of JavaScript timesamp, number pairs>,
        #       }, // ...
        #   },
        #   "query": {
        #       "start": <number>, // Javascript time stamp
        #       "duration": <number>, // milliseconds
        #   },
        # }

        self.assertEquals(response.status_code, 200)
        self.assertIsNotNone(response.json)

        link = response.json['link']
        self.assertEqual(link['id'], link_id)

        data = response.json['data']

        self.assertIn('query', response.json)
        query = response.json['query']
        self.assertIn('earlier', query)
        self.assertIn('later', query)

        self.assertIn('speed', data)
        self.assertIn('flow', data)
        self.assertIn('occupancy', data)

        log.info('Returned data: {0}'.format(data))
        total_value_count = 0
        for k, v in data.items():
            self.assertIn(k, ('speed', 'flow', 'occupancy'))
            self.assertIn('values', v)
            total_value_count += len(v['values'])
            for ts, obs in v['values']:
                self.assertTrue(ts > 0)
                self.assertTrue(ts >= query['start'])
                self.assertTrue(ts <= query['start'] + query['duration'])

    def parse_links_response(self, response):
        self.assertEqual(response.status_code, 200)
        data = response.json
        return (data['properties'], data['properties']['page'], data['features'])

    def parse_link_aliases_response(self, response):
        self.assertEqual(response.status_code, 200)
        data = response.json
        return (data['page'], data['aliases'])

    def make_resolve_link_aliases_request(self, aliases):
        body = { 'aliases': aliases }
        return self.client.post(API_PREFIX + '/aliases/resolve',
                data=json.dumps(body), content_type='application/json')
