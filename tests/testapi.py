import datetime
import logging
try:
    from urlparse import urljoin
    from urllib import urlencode
except ImportError:
    from urllib.parse import urljoin, urlencode

from .fixtures import create_fake_observations
from .util import TestCase

log = logging.getLogger(__name__)

API_PREFIX = '/api'

class TestApiRoot(TestCase):
    def test_api_root(self):
        response = self.client.get(API_PREFIX + '/')
        self.assertIsNot(response.json, None)
        log.info('Got response: {0}'.format(response.json))
        self.assertIn('version', response.json)
        self.assertEquals(response.json['version'], 1)

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

    def test_empty_links_document(self):
        from trafficdb.models import db, Link
        from sqlalchemy import func

        max_link_id = db.session.query(func.max(Link.id)).scalar()
        log.info('Maximum link id is: {0}'.format(max_link_id))

        log.info('Querying page beyond link list')
        query = { 'from': max_link_id + 100 }
        url = API_PREFIX + '/links?' + urlencode(query)
        response = self.client.get(url)
        self.assertIsNot(response.json, None)

        page = response.json['page']
        links = response.json['data']['features']

        self.assertEqual(len(links), 0)
        self.assertIsNone(page['first'])
        self.assertIsNone(page['last'])
        self.assertNotIn('next', page)

    def test_small_counts(self):
        from trafficdb.blueprint.api import PAGE_LIMIT
        request_count = max(1,PAGE_LIMIT >> 1)
        assert PAGE_LIMIT > request_count

        log.info('Querying {0} links'.format(request_count))
        query = { 'count': request_count }
        url = API_PREFIX + '/links?' + urlencode(query)
        response = self.client.get(url)
        self.assertIsNot(response.json, None)
        page = response.json['page']
        links = response.json['data']['features']
        self.assertEqual(len(links), request_count)
        self.assertEqual(len(links), page['count'])

    def test_huge_counts(self):
        from trafficdb.blueprint.api import PAGE_LIMIT

        log.info('Querying 100 links (should be truncated)')
        query = { 'count': PAGE_LIMIT * 4 }
        url = API_PREFIX + '/links?' + urlencode(query)
        response = self.client.get(url)
        self.assertIsNot(response.json, None)
        page = response.json['page']
        links = response.json['data']['features']
        self.assertEqual(len(links), page['count'])
        self.assertTrue(len(links) == PAGE_LIMIT)

    # Add a timeout in case of infinite loop
    def test_all_links(self):
        log.info('Querying all links')
        n_links = 0
        n_pages = 0

        # Response should look like:
        # {
        #   "data": <GeoJSON Feature collection>,
        #   "page": {
        #       "count": <number>,
        #       "first": <number>,
        #       "last": <number>,
        #       ?"next": <url>,
        #   },
        # }

        # Get all data one page at a time
        url = API_PREFIX + '/links'
        while url is not None:
            # Check we're not looping "forever"
            assert n_pages < 20

            log.info('GET {0}'.format(url))
            response = self.client.get(url)
            self.assertIsNot(response.json, None)

            page = response.json['page']
            links = response.json['data']['features']
            log.info('Got {0} links'.format(len(links)))
            log.info('Page structure: {0}'.format(page))

            n_links += len(links)

            self.assertTrue(page['last'] >= page['first'])
            self.assertTrue(page['count'] == len(links))

            n_pages += 1
            if 'next' in page:
                # Note that we need to strip the URL since our request
                # mock isn't clever enough to deal with it.
                url = page['next']
                prefix = 'http://localhost'
                if url.startswith(prefix):
                    url = url[len(prefix):]
            else:
                url = None

        log.info('Got information on {0} link(s)'.format(n_links))
        self.assertEqual(n_links, 104)

    def test_observations_for_non_existant_link(self):
        from trafficdb.models import db, Link
        from sqlalchemy import func

        max_link_id = db.session.query(func.max(Link.id)).scalar()
        log.info('Maximum link id is: {0}'.format(max_link_id))

        # Check that non-existent link returns 404
        log.info('Querying for non-existent link')
        response = self.client.get(API_PREFIX + '/observations/{0}'.format(max_link_id + 1))
        log.info('Got status: {0}'.format(response.status_code))
        self.assertEqual(response.status_code, 404)

    def test_observations_for_link(self):
        log.info('Querying first link')
        link_id = self.client.get(API_PREFIX + '/links?count=1').\
                json['data']['features'][0]['id']
        log.info('Querying for link {0}'.format(link_id))

        response = self.client.get(API_PREFIX + '/observations/{0}'.format(link_id))
        self.assertIsNotNone(response.json)

        # Response should look like:
        # {
        #   "link": {
        #       id: <number>,
        #   },
        #   "data": {
        #       <string>: {
        #           "values": <array of JavaScript timesamp, number pairs>,
        #       }, // ...
        #   }
        # }

        link = response.json['link']
        self.assertEqual(link['id'], link_id)

        data = response.json['data']

        self.assertIn('speed', data)

        log.info('Returned data: {0}'.format(data))
        total_value_count = 0
        for k, v in data.items():
            self.assertIn(k, ('speed', 'flow', 'occupancy'))
            self.assertIn('values', v)
            total_value_count += len(v['values'])
            for ts, obs in v['values']:
                self.assertTrue(ts > 0)
        self.assertTrue(total_value_count > 0)
