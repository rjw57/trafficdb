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

    def test_links_redirect(self):
        # Non-canonical links URL should re-direct
        url = API_PREFIX + '/links'
        log.info('GET {0}'.format(url))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 301)

    def test_empty_links_document(self):
        from trafficdb.models import db, Link
        from sqlalchemy import func

        log.info('Querying page beyond link list')
        query = { 'from': '_'*22 } # This is all 1s => highest UUID
        url = API_PREFIX + '/links/?' + urlencode(query)
        log.info('GET {0}'.format(url))
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertIsNot(response.json, None)

        page = response.json['page']
        links = response.json['data']['features']

        self.assertEqual(len(links), 0)
        self.assertNotIn('next', page)

    def test_negative_count(self):
        request_count = -3
        log.info('Querying {0} links'.format(request_count))
        query = { 'count': request_count }
        url = API_PREFIX + '/links/?' + urlencode(query)
        log.info('GET {0}'.format(url))
        response = self.client.get(url)
        # -ve counts should return bad request
        self.assertEqual(response.status_code, 400)

    def test_non_number_vount(self):
        request_count = 'one'
        query = { 'count': request_count }
        url = API_PREFIX + '/links/?' + urlencode(query)
        log.info('GET {0}'.format(url))
        response = self.client.get(url)
        # non-numeric counts should return bad request
        self.assertEqual(response.status_code, 400)

    def test_small_counts(self):
        from trafficdb.blueprint.api import PAGE_LIMIT
        request_count = max(1,PAGE_LIMIT >> 1)
        assert PAGE_LIMIT > request_count

        log.info('Querying {0} links'.format(request_count))
        query = { 'count': request_count }
        url = API_PREFIX + '/links/?' + urlencode(query)
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
        url = API_PREFIX + '/links/?' + urlencode(query)
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

            page = response.json['page']
            links = response.json['data']['features']
            log.info('Got {0} links'.format(len(links)))
            log.info('Page structure: {0}'.format(page))

            n_links += len(links)

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

        # Check that non-existent link returns 404
        log.info('Querying for non-existent link')
        url = API_PREFIX + '/links/{0}/observations'.format('X'*22)
        log.info('GET {0}'.format(url))
        response = self.client.get(url)
        log.info('Got status: {0}'.format(response.status_code))
        self.assertEqual(response.status_code, 404)

    def test_observations_for_link(self):
        log.info('Querying first link')
        link_id = self.client.get(API_PREFIX + '/links/?count=1').\
                json['data']['features'][0]['id']
        log.info('Querying for link {0}'.format(link_id))

        response = self.client.get(API_PREFIX + '/links/{0}/observations'.format(link_id))
        self.assertEquals(response.status_code, 200)
        self.assertIsNotNone(response.json)

        # Response should look like:
        # {
        #   "link": {
        #       id: <string>,
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
