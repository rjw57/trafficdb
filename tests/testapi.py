import datetime
import logging
try:
    from urlparse import urljoin
    from urllib import urlencode
except ImportError:
    from urllib.parse import urljoin, urlencode

from .fixtures import (
    create_fake_link_aliases,
    create_fake_links,
    create_fake_observations,
)
from .util import TestCase as BaseTestCase

log = logging.getLogger(__name__)

API_PREFIX = '/api'

def strip_url(url):
    """Strip leading http://localhost from URLs since our client mock doesn't
    deal with it.

    """
    prefix = 'http://localhost'
    if url.startswith(prefix):
        url = url[len(prefix):]
    return url

class TestCase(BaseTestCase):
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
            url = API_PREFIX + '/linkaliases/',
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
        from trafficdb.models import db, Link
        n_links = db.session.query(Link.id).count()
        log.info('Total links: {0}'.format(n_links))
        self.assertEqual(n_links, 104)

    def test_links_redirect(self):
        # Non-canonical links URL should re-direct
        url = API_PREFIX + '/links'
        log.info('GET {0}'.format(url))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 301)

    def test_empty_links_document(self):
        log.info('Querying page beyond link list')
        response = self.get_links(
            from_ = '_' * 22 # This is all 1s => highest UUID
        )
        properties, page, links = self.parse_links_response(response)
        self.assertEqual(len(links), 0)
        self.assertNotIn('next', page)

    def test_integer_from(self):
        log.info('Querying page with integer from')
        response = self.get_links(from_=0)
        self.assertEqual(response.status_code, 400)

    def test_negative_count(self):
        request_count = -3
        log.info('Querying {0} links'.format(request_count))
        response = self.get_links(count=request_count)
        # -ve counts should return bad request
        self.assertEqual(response.status_code, 400)

    def test_non_number_count(self):
        request_count = 'one'
        log.info('Querying {0} links'.format(request_count))
        response = self.get_links(count=request_count)
        # non-numeric counts should return bad request
        self.assertEqual(response.status_code, 400)

    def test_small_counts(self):
        from trafficdb.blueprint.api import PAGE_LIMIT
        request_count = max(1,PAGE_LIMIT >> 1)
        assert PAGE_LIMIT > request_count

        log.info('Querying {0} links'.format(request_count))
        response = self.get_links(count=request_count)
        properties, page, links = self.parse_links_response(response)
        self.assertEqual(len(links), request_count)
        self.assertEqual(len(links), page['count'])

    def test_huge_counts(self):
        from trafficdb.blueprint.api import PAGE_LIMIT
        log.info('Querying 100 links (should be truncated)')
        request_count = PAGE_LIMIT * 4
        log.info('Querying {0} links'.format(request_count))
        response = self.get_links(count=request_count)
        properties, page, links = self.parse_links_response(response)
        self.assertEqual(len(links), page['count'])
        self.assertTrue(len(links) == PAGE_LIMIT)

    def test_all_links(self):
        log.info('Querying all links')
        n_links = 0
        n_pages = 0

        # Response should look like a GeoJSON feature collection with
        # properties of the following form:
        # {
        #   "page": {
        #       "count": <number>,
        #       ?"next": <url>,
        #   },
        # }

        # Get all data one page at a time
        url = API_PREFIX + '/links/'
        while url is not None:
            # Check we're not looping "forever"
            assert n_pages < 20

            log.info('GET {0}'.format(url))
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertIsNot(response.json, None)

            self.assertIn('properties', response.json)
            self.assertEqual(response.json['type'], 'FeatureCollection')

            properties = response.json['properties']
            links = response.json['features']
            page = properties['page']

            log.info('Got {0} links'.format(len(links)))
            log.info('Page structure: {0}'.format(page))

            n_links += len(links)

            self.assertTrue(page['count'] == len(links))

            n_pages += 1
            if 'next' in page:
                url = strip_url(page['next'])
            else:
                url = None

        log.info('Got information on {0} link(s)'.format(n_links))
        self.assertEqual(n_links, 104)

    def test_observations_for_non_existant_link(self):
        from trafficdb.models import db, Link
        from sqlalchemy import func

        # Check that non-existent link returns 404
        log.info('Querying for non-existent link')
        response = self.get_observations('X'*22)
        log.info('Got status: {0}'.format(response.status_code))
        self.assertEqual(response.status_code, 404)

    def test_observations_for_bad_link(self):
        from trafficdb.models import db, Link
        from sqlalchemy import func

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

    def test_invalid_link_information_query(self):
        url = strip_url(API_PREFIX + '/links/10/')
        log.info('Querying for link at {0}'.format(url))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_non_existant_link_information_query(self):
        url = strip_url(API_PREFIX + '/links/{0}/'.format('X'*22))
        log.info('Querying for link at {0}'.format(url))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_link_information_query(self):
        log.info('Querying first link')
        link_feature = self.get_links(count=1).json['features'][0]

        url = strip_url(link_feature['properties']['url'])
        log.info('Querying for link at {0}'.format(url))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json)

        # Response should look like:
        # {
        #   id: <string>,
        #   observarionsUrl: <url>,
        # }

        self.assertIn('id', response.json)
        self.assertEqual(response.json['id'], link_feature['id'])
        self.assertIn('observationsUrl', response.json)

class TestLinkAliases(TestCase):
    @classmethod
    def create_fixtures(cls):
        create_fake_links(link_count=100)
        create_fake_link_aliases(alias_count=200)

    def test_all_link_aliass(self):
        log.info('Querying all link aliases')
        n_aliases = 0
        n_pages = 0

        # Response should look like a JSON document of the following form:
        # {
        #   "aliases": [
        #       {
        #           id: <string>,
        #           linkId: <string>,
        #           linkUrl: <url>,
        #       }
        #   ],
        #   "page": {
        #       "count": <number>,
        #       ?"next": <url>,
        #   },
        # }

        # Get all data one page at a time
        url = API_PREFIX + '/linkaliases/'
        while url is not None:
            # Check we're not looping "forever"
            assert n_pages < 20

            log.info('GET {0}'.format(url))
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertIsNot(response.json, None)

            self.assertIn('aliases', response.json)
            self.assertIn('page', response.json)

            aliases = response.json['aliases']
            page = response.json['page']

            log.info('Got {0} aliases'.format(len(aliases)))
            log.info('Page structure: {0}'.format(page))

            # Check each alias
            for v in aliases:
                self.assertIn('id', v)
                self.assertIn('linkId', v)
                self.assertIn('linkUrl', v)

            n_aliases += len(aliases)

            self.assertTrue(page['count'] == len(aliases))

            n_pages += 1
            if 'next' in page:
                url = strip_url(page['next'])
            else:
                url = None

        log.info('Got information on {0} alias(es)'.format(n_aliases))
        self.assertEqual(n_aliases, 200)

    def test_redirect(self):
        # Non-canonical links URL should re-direct
        url = API_PREFIX + '/linkaliases'
        log.info('GET {0}'.format(url))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 301)

    def test_empty_document(self):
        log.info('Querying page beyond alias maximum')
        # rationale: using "Z" should be "above" any
        # random link alias in the db given the ordering used by Postgres.
        response = self.get_link_aliases(from_='Z')
        page, aliases = self.parse_link_aliases_response(response)
        self.assertEqual(len(aliases), 0)
        self.assertNotIn('next', page)

    def test_integer_from(self):
        # In the case of aliases, names can be just about anything and
        # so they could be an integer.
        log.info('Querying page with integer from')
        response = self.get_link_aliases(from_=0)
        page, aliases = self.parse_link_aliases_response(response)

    def test_negative_count(self):
        request_count = -3
        log.info('Querying {0} aliases'.format(request_count))
        response = self.get_link_aliases(count=request_count)
        # -ve counts should return bad request
        self.assertEqual(response.status_code, 400)

    def test_non_number_count(self):
        request_count = 'one'
        log.info('Querying {0} aliases'.format(request_count))
        response = self.get_link_aliases(count=request_count)
        # non-numeric counts should return bad request
        self.assertEqual(response.status_code, 400)

    def test_small_counts(self):
        from trafficdb.blueprint.api import PAGE_LIMIT
        request_count = max(1,PAGE_LIMIT >> 1)
        assert PAGE_LIMIT > request_count

        log.info('Querying {0} aliases'.format(request_count))
        response = self.get_link_aliases(count=request_count)
        page, aliases = self.parse_link_aliases_response(response)
        self.assertEqual(len(aliases), request_count)
        self.assertEqual(len(aliases), page['count'])

    def test_huge_counts(self):
        from trafficdb.blueprint.api import PAGE_LIMIT
        log.info('Querying 100 aliases (should be truncated)')
        request_count = PAGE_LIMIT * 4
        log.info('Querying {0} aliases'.format(request_count))
        response = self.get_link_aliases(count=request_count)
        page, aliases = self.parse_link_aliases_response(response)
        self.assertEqual(len(aliases), page['count'])
        self.assertTrue(len(aliases) == PAGE_LIMIT)
