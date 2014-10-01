import datetime
import logging
import random

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
        url = API_PREFIX + '/aliases/'
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
        url = API_PREFIX + '/aliases'
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
        request_count = max(1,PAGE_LIMIT >> 1)
        assert PAGE_LIMIT > request_count

        log.info('Querying {0} aliases'.format(request_count))
        response = self.get_link_aliases(count=request_count)
        page, aliases = self.parse_link_aliases_response(response)
        self.assertEqual(len(aliases), request_count)
        self.assertEqual(len(aliases), page['count'])

    def test_huge_counts(self):
        log.info('Querying 100 aliases (should be truncated)')
        request_count = PAGE_LIMIT * 4
        log.info('Querying {0} aliases'.format(request_count))
        response = self.get_link_aliases(count=request_count)
        page, aliases = self.parse_link_aliases_response(response)
        self.assertEqual(len(aliases), page['count'])
        self.assertTrue(len(aliases) == PAGE_LIMIT)

    def test_non_json_resolve_body(self):
        response = self.client.post(API_PREFIX + '/aliases/resolve',
                data='not a json document', content_type='application/json')
        self.assert_400(response)

    def test_empty_json_resolve_body(self):
        response = self.client.post(API_PREFIX + '/aliases/resolve',
                data='{}', content_type='application/json')
        self.assert_400(response)

    def test_bad_alias_list_resolve_body_1(self):
        response = self.client.post(API_PREFIX + '/aliases/resolve',
                data='{"aliases": 3}', content_type='application/json')
        self.assert_400(response)

    def test_bad_alias_list_resolve_body_1(self):
        response = self.client.post(API_PREFIX + '/aliases/resolve',
                data='{"aliases": ["one", 3]}', content_type='application/json')
        self.assert_400(response)

    def test_bad_content_type_resolve_body(self):
        response = self.client.post(API_PREFIX + '/aliases/resolve',
                data='{"aliases": []}', content_type='text/plain')
        self.assert_400(response)

    def test_empty_resolve(self):
        response = self.make_resolve_link_aliases_request([])
        self.assert_200(response)
        self.assertIn('resolutions', response.json)
        resolutions = response.json['resolutions']
        self.assertEqual(len(resolutions), 0)

    def gen_alias_names(self, good_count=3, bad_count=3):
        good_alias_names = set(r[0] for r in db.session.query(LinkAlias.name))
        bad_alias_names = set('_bad_alias_{0}'.format(x) for x in range(bad_count))
        alias_names = random.sample(good_alias_names, good_count) + list(bad_alias_names)
        random.shuffle(alias_names)
        return dict((n, n in good_alias_names) for n in alias_names)

    def test_simple_resolve(self):
        alias_name_map = self.gen_alias_names()
        query_names = list(alias_name_map.keys())
        log.info('Querying aliases: {0}'.format(query_names))
        response = self.make_resolve_link_aliases_request(query_names)
        self.assert_200(response)
        self.assertIn('resolutions', response.json)
        resolutions = response.json['resolutions']
        log.info('Resolutions: {0}'.format(resolutions))
        self.assertEqual(len(resolutions), len(query_names))
        for name, res in zip(query_names, resolutions):
            res_name, res_link = res
            self.assertEqual(name, res_name)
            if alias_name_map[name]:
                # good link
                self.assertIsNotNone(res_link)
                self.assertIn('id', res_link)
                self.assertIn('url', res_link)
            else:
                # bad link
                self.assertIsNone(res_link)

    def test_single_good_resolve(self):
        alias_name_map = self.gen_alias_names(good_count=1, bad_count=0)
        query_names = list(alias_name_map.keys())
        log.info('Querying aliases: {0}'.format(query_names))
        response = self.make_resolve_link_aliases_request(query_names)
        self.assert_200(response)
        self.assertIn('resolutions', response.json)
        resolutions = response.json['resolutions']
        log.info('Resolutions: {0}'.format(resolutions))
        self.assertEqual(len(resolutions), len(query_names))
        for name, res in zip(query_names, resolutions):
            res_name, res_link = res
            self.assertEqual(name, res_name)
            if alias_name_map[name]:
                # good link
                self.assertIsNotNone(res_link)
                self.assertIn('id', res_link)
                self.assertIn('url', res_link)
            else:
                # bad link
                self.assertIsNone(res_link)

    def test_single_bad_resolve(self):
        alias_name_map = self.gen_alias_names(good_count=0, bad_count=1)
        query_names = list(alias_name_map.keys())
        log.info('Querying aliases: {0}'.format(query_names))
        response = self.make_resolve_link_aliases_request(query_names)
        self.assert_200(response)
        self.assertIn('resolutions', response.json)
        resolutions = response.json['resolutions']
        log.info('Resolutions: {0}'.format(resolutions))
        self.assertEqual(len(resolutions), len(query_names))
        for name, res in zip(query_names, resolutions):
            res_name, res_link = res
            self.assertEqual(name, res_name)
            if alias_name_map[name]:
                # good link
                self.assertIsNotNone(res_link)
                self.assertIn('id', res_link)
                self.assertIn('url', res_link)
            else:
                # bad link
                self.assertIsNone(res_link)

    def test_too_big_resolve(self):
        alias_name_map = self.gen_alias_names(good_count=PAGE_LIMIT, bad_count=PAGE_LIMIT)
        query_names = list(alias_name_map.keys())
        log.info('Querying aliases: {0}'.format(query_names))
        response = self.make_resolve_link_aliases_request(query_names)
        self.assert_400(response)
