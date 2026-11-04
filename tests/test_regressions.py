"""Offline error, pagination, validation and file-safety regressions."""
from copy import deepcopy
from io import BytesIO
import json
from io import StringIO
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import collect_stats
import render_assets
import test_generator


class CollectorTests(unittest.TestCase):
    def setUp(self):
        fixture = test_generator.ProfileTests()
        fixture.setUp()
        self.page = fixture.one
        self.page['repositories']['pageInfo'] = {'hasNextPage': False, 'endCursor': None}

    def test_collect_follows_pages(self):
        first = deepcopy(self.page)
        first['repositories']['pageInfo'] = {'hasNextPage': True, 'endCursor': 'next'}
        second = deepcopy(self.page)
        second['repositories']['nodes'] = []
        with patch.object(collect_stats, 'query_graphql', side_effect=[first, second]) as query:
            self.assertEqual(collect_stats.collect('Starblood24', 'secret')['public_repositories'], 1)
        self.assertEqual(query.call_args_list[1].args[2], 'next')

    def test_collect_rejects_bad_pagination_and_wrong_user(self):
        for change in ('missing', 'cycle', 'wrong-user'):
            with self.subTest(change=change):
                page = deepcopy(self.page)
                if change == 'missing':
                    del page['repositories']['pageInfo']
                elif change == 'cycle':
                    page['repositories']['pageInfo'] = {'hasNextPage': True, 'endCursor': 'repeat'}
                else:
                    page['login'] = 'another-user'
                with patch.object(collect_stats, 'query_graphql', return_value=page):
                    with self.assertRaises((ValueError, RuntimeError)):
                        collect_stats.collect('Starblood24', 'secret')

    def test_rejects_missing_repositories_and_truncated_languages(self):
        for change in ('repositories', 'languages', 'negative', 'boolean', 'bad-date', 'duplicate-day'):
            with self.subTest(change=change):
                page = deepcopy(self.page)
                if change == 'repositories':
                    page.pop('repositories')
                elif change == 'languages':
                    page['repositories']['nodes'][0]['languages']['pageInfo'] = {'hasNextPage': True}
                elif change in ('negative', 'boolean'):
                    page['repositories']['nodes'][0]['stargazerCount'] = -1 if change == 'negative' else True
                elif change == 'bad-date':
                    page['contributionsCollection']['contributionCalendar']['weeks'][0]['contributionDays'][0]['date'] = '2026-13-01'
                else:
                    days = page['contributionsCollection']['contributionCalendar']['weeks'][0]['contributionDays']
                    days.append(deepcopy(days[0]))
                with self.assertRaises(ValueError):
                    collect_stats.normalize_profile([page], 'Starblood24', '2026-11-04')

    def test_network_errors_and_graphql_errors_do_not_echo_secrets(self):
        for error in (HTTPError('url', 401, 'secret', {}, None), URLError('secret'), TimeoutError('secret')):
            with self.subTest(error=type(error).__name__), patch.object(collect_stats, 'urlopen', side_effect=error):
                with self.assertRaises(RuntimeError) as caught:
                    collect_stats.query_graphql('secret', 'Starblood24', None)
                self.assertNotIn('secret', str(caught.exception))
        with patch.object(collect_stats, 'urlopen', return_value=BytesIO(b'{"errors":[{"message":"secret"}]}')):
            with self.assertRaises(RuntimeError) as caught:
                collect_stats.query_graphql('secret', 'Starblood24', None)
            self.assertNotIn('secret', str(caught.exception))

    def test_failed_collection_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)/'stats.json'
            target.write_text('previous snapshot', encoding='utf-8')
            with patch.dict('os.environ', {'GITHUB_TOKEN':'secret'}), patch.object(sys, 'argv', ['collect_stats', '--output', str(target)]), patch.object(collect_stats, 'collect', side_effect=ValueError('Invalid response')), patch('sys.stderr', new=StringIO()):
                self.assertEqual(collect_stats.main(), 1)
            self.assertEqual(target.read_text(encoding='utf-8'), 'previous snapshot')
            self.assertFalse(target.with_suffix('.json.tmp').exists())

    def test_missing_token_never_requests_or_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)/'missing.json'
            with patch.dict('os.environ', {}, clear=True), patch.object(sys, 'argv', ['collect_stats', '--output', str(target)]), patch.object(collect_stats, 'query_graphql') as query, patch('sys.stderr', new=StringIO()):
                self.assertEqual(collect_stats.main(), 2)
                query.assert_not_called()
            self.assertFalse(target.exists())


class RendererTests(unittest.TestCase):
    def setUp(self):
        self.demo = json.loads((ROOT/'tests/fixtures/demo_stats.json').read_text(encoding='utf-8'))

    def test_validation_precedes_all_file_writes(self):
        for change in ('negative', 'boolean', 'status', 'dates', 'language'):
            data = deepcopy(self.demo)
            if change == 'negative':
                data['total_stars'] = -1
            elif change == 'boolean':
                data['total_stars'] = True
            elif change == 'status':
                data['status'] = 'unknown'
            elif change == 'dates':
                data['days'] = [{'date':'not-a-date', 'count':0}]
            else:
                data['languages'][0]['bytes'] = -1
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                target = Path(directory)/'stats.svg'
                target.write_text('previous', encoding='utf-8')
                with self.assertRaises(ValueError):
                    render_assets.render_into(data, Path(directory))
                self.assertEqual(target.read_text(encoding='utf-8'), 'previous')
                self.assertEqual(len(list(Path(directory).iterdir())), 1)

    def test_empty_live_languages_are_not_pending(self):
        self.demo.update(status='live', languages=[])
        self.assertIn('NO ELIGIBLE LANGUAGE DATA', render_assets.render_languages(self.demo))
        self.assertIn('NO ELIGIBLE LANGUAGE DATA', render_assets.render_languages_mobile(self.demo))

    def test_every_mobile_telemetry_panel_labels_demo(self):
        for render in (render_assets.render_stats_mobile, render_assets.render_contributions_mobile, render_assets.render_languages_mobile):
            self.assertIn('DEMO DATA', render(self.demo))

    def test_language_text_is_xml_escaped(self):
        self.demo['languages'][0]['name'] = '<script>&"'
        with tempfile.TemporaryDirectory() as directory:
            render_assets.render_into(self.demo, Path(directory))
            for target in Path(directory).glob('*.svg'):
                svg = ET.parse(target)
                self.assertFalse(svg.findall('.//{http://www.w3.org/2000/svg}script'))


if __name__ == '__main__':
    unittest.main()
