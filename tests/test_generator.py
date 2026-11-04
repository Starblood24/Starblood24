"""Offline regression tests; run: python -m unittest discover -s tests -v."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import collect_stats
import render_assets


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.calendar={"totalContributions":4,"weeks":[{"contributionDays":[{"date":"2026-11-01","contributionCount":4}]}]}
        self.one={"login":"Starblood24", "contributionsCollection":{"contributionCalendar":self.calendar},
                  "repositories":{"nodes":[{"name":"typr","stargazerCount":3,"forkCount":1,"isFork":False,"isArchived":False,
                                            "languages":{"pageInfo":{"hasNextPage":False},"edges":[{"size":30,"node":{"name":"Python"}}]}}]}}
        self.two={"login":"Starblood24", "repositories":{"nodes":[{"name":"game","stargazerCount":2,"forkCount":0,"isFork":True,"isArchived":False,
                                                                 "languages":{"pageInfo":{"hasNextPage":False},"edges":[{"size":300,"node":{"name":"JavaScript"}}]}}]}}

    def test_normalization_all_pages_and_language_filter(self):
        out=collect_stats.normalize_profile([self.one,self.two],"Starblood24","2026-11-04T00:00:00+00:00")
        self.assertEqual(out["public_repositories"],2)
        self.assertEqual(out["total_stars"],5)
        self.assertEqual(out["total_forks"],1)
        self.assertEqual(out["year_contributions"],4)
        self.assertEqual(out["languages"][0]["name"],"Python")
        self.assertEqual(len(out["languages"]),1)
        self.assertEqual(out["days"][0]["date"],"2026-11-01")

    def test_no_absent_calendar_fabricated(self):
        one=dict(self.one)
        one["contributionsCollection"]={}
        with self.assertRaises(ValueError):
            collect_stats.normalize_profile([one],"Starblood24","2026-11-04")

    def test_xml_escaped(self):
        self.assertIn("&lt;script&gt;", render_assets.txt(1,2,"<script>",size=12))

    def test_pending_contains_no_invented_values(self):
        data={"status":"pending"}
        stats=render_assets.render_stats(data)
        self.assertIn("AWAITING FIRST API RUN",stats)
        self.assertIn("—",stats)
        self.assertNotIn(">382<",stats)

    def test_rendered_svg_valid(self):
        demo=json.loads((ROOT/"tests/fixtures/demo_stats.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            render_assets.render_into(demo,Path(directory))
            for name in ["stats.svg","contributions.svg","languages.svg", "stats_mobile.svg", "contributions_mobile.svg", "languages_mobile.svg"]:
                with self.subTest(name=name):
                    ET.parse(Path(directory)/name)
            self.assertIn("DEMO DATA",(Path(directory)/"stats.svg").read_text())

    def test_non_ascii_avatar_is_actual_svg_text(self):
        svg=(ROOT/"assets/avatar_ascii.svg").read_text()
        ET.fromstring(svg)
        self.assertIn("<text ",svg)
        self.assertNotIn("<image",svg)

    def test_illustration_assets_are_valid_svg(self):
        for name in ["hero.svg", "hero_mobile.svg", "featured_typr.svg", "featured_typr_mobile.svg", "stack.svg", "stack_mobile.svg"]:
            with self.subTest(name=name):
                ET.parse(ROOT/"assets"/name)

    def test_workflow_never_commits_demo(self):
        workflow=(ROOT/".github/workflows/update-profile.yml").read_text()
        self.assertIn("secrets.GITHUB_TOKEN",workflow)
        self.assertIn("workflow_dispatch",workflow)
        self.assertIn('branches: [main]', workflow)
        self.assertIn("'scripts/collect_stats.py'", workflow)
        self.assertNotIn("preview/demo",workflow)
        self.assertRegex(workflow, r'actions/checkout@[0-9a-f]{40}')
        self.assertRegex(workflow, r'actions/setup-python@[0-9a-f]{40}')
        self.assertIn('github.event.repository.default_branch', workflow)
        self.assertLess(workflow.index('python -m unittest'), workflow.index('python scripts/collect_stats.py'))
        self.assertNotIn('pull_request', workflow)


if __name__=="__main__":
    unittest.main()
