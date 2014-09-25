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
        self.assertEquals(response.json, dict(version=1))

class TestSimpleQueries(TestCase):
    def create_fixtures(self):
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

    def test_all_links(self):
        log.info('Querying all links')
        query = None
        n_links = 0
        while True:
            url = API_PREFIX + '/links'
            if query is not None:
                url += '?' + urlencode(query)

            log.info('GET {0}'.format(url))
            response = self.client.get(url)
            self.assertIsNot(response.json, None)

            page = response.json['page']
            links = response.json['data']
            log.info('Got {0} links'.format(len(links)))
            log.info('Page structure: {0}'.format(page))

            n_links += len(links)

            if query is not None:
                self.assertTrue(page['first'] >= query['from'])

            self.assertTrue(page['last'] >= page['first'])
            self.assertTrue(page['count'] == len(links))

            if not page['more']:
                break

            query = query or {}
            query['from'] = page['last'] + 1

        log.info('Got information on {0} link(s)'.format(n_links))
        self.assertEqual(n_links, 104)
