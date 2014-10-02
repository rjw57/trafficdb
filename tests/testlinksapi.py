import datetime
import json
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

class TestIndex(TestCase):
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
        # Server returns 404 to avoid leaking information on link id format
        self.assertEqual(response.status_code, 404)

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
        request_count = max(1,PAGE_LIMIT >> 1)
        assert PAGE_LIMIT > request_count

        log.info('Querying {0} links'.format(request_count))
        response = self.get_links(count=request_count)
        properties, page, links = self.parse_links_response(response)
        self.assertEqual(len(links), request_count)
        self.assertEqual(len(links), page['count'])

    def test_huge_counts(self):
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

class TestSingleLink(TestCase):
    @classmethod
    def create_fixtures(cls):
        start_date = datetime.datetime(2013, 9, 10)

        # NOTE: total links is 20
        create_fake_observations(link_count=20, start=start_date, duration=60)

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
        #   type: "Feature",
        #   geometry: {
        #       type: "LineString",
        #       coordinates: <array of co-ordinates>,
        #   },
        #   properties: {
        #       observationsUrl: <url>,
        #       aliases: <array of string>,
        #   },
        # }
        self.assertIn('properties', response.json)
        self.assertIn('type', response.json)
        self.assertIn('geometry', response.json)
        self.assertIn('id', response.json)

        id, type, geometry, properties = tuple(
                response.json[x] for x in ('id', 'type', 'geometry', 'properties'))
        self.assertEqual(type, 'Feature')

        self.assertEqual(id, link_feature['id'])
        self.assertEqual(geometry['type'], 'LineString')
        self.assertIn('coordinates', geometry)

        self.assertIn('observationsUrl', properties)
        self.assert_200(self.client.get(strip_url(properties['observationsUrl'])))

LINKS_PATH = API_PREFIX + '/links/'

class TestMutation(TestCase):
    @classmethod
    def create_fixtures(cls):
        create_fake_links(link_count=20)

    def new_link_request(self, link_data):
        return self.client.patch(LINKS_PATH,
                data=json.dumps(link_data),
                content_type='application/json')

    def test_empty_body_request(self):
        response = self.client.patch(LINKS_PATH, data='', content_type='application/json')
        self.assert_400(response)

    def test_non_json_body_request(self):
        response = self.client.patch(LINKS_PATH, data='not json', content_type='application/json')
        self.assert_400(response)

    def test_no_content_type_body_request(self):
        response = self.client.patch(LINKS_PATH, data='{}')
        self.assert_400(response)

    def test_empty_request(self):
        response = self.new_link_request({})
        self.assert_200(response)

    def verify_create(self, create, response):
        self.assert_200(response)
        self.assertIn('create', response.json)
        create_resp = response.json['create']
        self.assertEqual(len(create_resp), len(create))

        for req, link in zip(create, create_resp):
            self.assertIn('id', link)
            self.assertIn('url', link)
            url = strip_url(link['url'])
            link_resp = self.client.get(url)
            self.assert_200(link_resp)
            link_coords = link_resp.json['geometry']['coordinates']
            self.assertEqual(link_coords, req['coordinates'])

    def test_create_single(self):
        create = [
            {
                'coordinates': [[-3, 46], [-2,47], [-1,48]],
            },
        ]
        response = self.new_link_request(dict(create=create))
        self.verify_create(create, response)

    def test_create_multiple(self):
        create = [
            { 'coordinates': [[-3, 46], [-2,47], [-1,48]], },
            { 'coordinates': [[-8, 46], [-2,47], [-1,48]], },
            { 'coordinates': [[-3, 36], [-2,67], [-0,18]], },
        ]
        response = self.new_link_request(dict(create=create))
        self.verify_create(create, response)
