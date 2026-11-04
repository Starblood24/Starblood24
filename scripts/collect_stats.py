#!/usr/bin/env python3
"""Read-only GitHub GraphQL collector for STARBLOOD.OS.

Standard library only. Exits nonzero before touching output if the API fails.
The workflow token is read exclusively from GITHUB_TOKEN/GH_TOKEN.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_URL = "https://api.github.com/graphql"
QUERY = """
query Profile($login: String!, $cursor: String) {
  user(login: $login) {
    login
    repositories(
      first: 100, after: $cursor, ownerAffiliations: OWNER,
      privacy: PUBLIC, orderBy: {field: UPDATED_AT, direction: DESC}
    ) {
      pageInfo { hasNextPage endCursor }
      nodes {
        name
        isFork
        isArchived
        stargazerCount
        forkCount
        languages(first: 100, orderBy: {field: SIZE, direction: DESC}) {
          pageInfo { hasNextPage }
          edges { size node { name } }
        }
      }
    }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def query_graphql(token: str, login: str, cursor: str | None) -> dict:
    payload = json.dumps({"query": QUERY, "variables": {"login": login, "cursor": cursor}}).encode("utf-8")
    request = Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "starblood-os-readme-stats",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=25) as response:
            result = json.load(response)
    except HTTPError as ex:
        # Never log request headers, token, or raw body (which might contain secrets).
        raise RuntimeError(f"GitHub HTTP {ex.code} — verify token access and rate limits") from None
    except (URLError, TimeoutError) as ex:
        raise RuntimeError(f"GitHub API network error: {type(ex).__name__}") from None
    if not isinstance(result, dict):
        raise ValueError("Invalid GraphQL response")
    if result.get("errors"):
        raise RuntimeError("GitHub GraphQL query failed; verify account access and rate limits")
    data = result.get("data")
    if not isinstance(data, dict):
        raise ValueError("Missing GraphQL data")
    user = data.get("user")
    if not isinstance(user, dict) or not user:
        raise RuntimeError("GitHub account not found or response incomplete")
    return user


def normalize_profile(pages: list[dict], login: str, updated_at: str) -> dict:
    if not pages:
        raise ValueError("At least one GraphQL response is required")
    first = pages[0]
    collection = first.get("contributionsCollection")
    if not isinstance(collection, dict) or not isinstance(collection.get("contributionCalendar"), dict):
        raise ValueError("Contribution calendar absent")
    calendar = collection["contributionCalendar"]
    if type(calendar.get("totalContributions")) is not int or calendar["totalContributions"] < 0 or not isinstance(calendar.get("weeks"), list):
        raise ValueError("Contribution calendar absent; refusing to display fabricated zeros")
    days = []
    for week in calendar["weeks"]:
        if not isinstance(week, dict) or not isinstance(week.get("contributionDays"), list):
            raise ValueError("Invalid contribution week")
        for day in week["contributionDays"]:
            if not isinstance(day, dict):
                raise ValueError("Invalid contribution day")
            day_date = day.get("date")
            count = day.get("contributionCount")
            if not isinstance(day_date, str) or type(count) is not int or count < 0:
                raise ValueError("Invalid calendar day")
            if date.fromisoformat(day_date).isoformat() != day_date:
                raise ValueError("Invalid calendar date")
            days.append({"date": day_date, "count": count})
    days.sort(key=lambda d: d["date"])
    if not days or len({d['date'] for d in days}) != len(days):
        raise ValueError("Empty or duplicate contribution days")
    all_repos = []
    language_bytes = defaultdict(int)
    for page in pages:
        repositories = page.get("repositories")
        if not isinstance(repositories, dict) or not isinstance(repositories.get("nodes"), list):
            raise ValueError("Repository data absent; refusing partial statistics")
        for repo in repositories["nodes"]:
            if not isinstance(repo, dict) or any(type(repo.get(key)) is not int or repo[key] < 0
                                                 for key in ("stargazerCount", "forkCount")):
                raise ValueError("Invalid repository counts")
            if any(type(repo.get(key)) is not bool for key in ("isFork", "isArchived")):
                raise ValueError("Missing repository flags")
            all_repos.append(repo)
            if repo.get("isFork") or repo.get("isArchived"):
                continue
            languages = repo.get("languages")
            if not isinstance(languages, dict) or not isinstance(languages.get("edges"), list):
                raise ValueError("Repository languages absent")
            page_info = languages.get("pageInfo")
            if not isinstance(page_info, dict) or type(page_info.get("hasNextPage")) is not bool:
                raise ValueError("Missing language pagination metadata")
            if page_info["hasNextPage"]:
                raise ValueError("Repository exceeds 100 languages; refusing truncated proportions")
            for edge in languages["edges"]:
                if not isinstance(edge, dict):
                    raise ValueError("Invalid language edge")
                node = edge.get("node")
                if not isinstance(node, dict):
                    raise ValueError("Invalid language node")
                name = node.get("name")
                size = edge.get("size")
                if not isinstance(name, str) or not name or type(size) is not int or size < 0:
                    raise ValueError("Invalid language entry")
                if size > 0:
                    language_bytes[name] += size
    total_bytes = sum(language_bytes.values())
    language_stats = [
        {"name": name, "bytes": size, "percent": round(100 * size / total_bytes, 1)}
        for name, size in sorted(language_bytes.items(), key=lambda x: (-x[1], x[0]))
    ] if total_bytes else []
    return {
        "schema_version": 1,
        "username": login,
        "updated_at": updated_at,
        "status": "live",
        "public_repositories": len(all_repos),
        "total_stars": sum(int(r.get("stargazerCount") or 0) for r in all_repos),
        "total_forks": sum(int(r.get("forkCount") or 0) for r in all_repos),
        "year_contributions": calendar["totalContributions"],
        "days": days,
        "languages": language_stats,
    }


def collect(login: str, token: str) -> dict:
    pages = []
    cursor = None
    seen_cursors = set()
    for _ in range(100):  # hard upper bound protects against broken pagination
        user = query_graphql(token, login, cursor)
        if not isinstance(user.get("login"), str) or user["login"].lower() != login.lower():
            raise RuntimeError("GitHub returned the wrong user")
        pages.append(user)
        repositories = user.get("repositories")
        if not isinstance(repositories, dict):
            raise ValueError("Repository data absent")
        page_info = repositories.get("pageInfo")
        if not isinstance(page_info, dict) or type(page_info.get("hasNextPage")) is not bool:
            raise ValueError("Missing repository pagination metadata")
        if not page_info["hasNextPage"]:
            break
        next_cursor = page_info.get("endCursor")
        if not isinstance(next_cursor, str) or not next_cursor or next_cursor in seen_cursors:
            raise RuntimeError("GitHub pagination cursor did not advance")
        cursor = next_cursor
        seen_cursors.add(cursor)
    else:
        raise RuntimeError("GitHub pagination safety limit reached")
    return normalize_profile(pages, login, datetime.now(timezone.utc).isoformat(timespec="seconds"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect public GitHub profile statistics")
    parser.add_argument("--username", default="Starblood24")
    parser.add_argument("--output", default="data/stats.json")
    args = parser.parse_args()
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN (or GH_TOKEN) is not set. No files were changed.", file=sys.stderr)
        return 2
    try:
        result = collect(args.username, token)
    except (RuntimeError, ValueError) as ex:
        print(f"ERROR: {ex}. Previous generated assets are left unchanged.", file=sys.stderr)
        return 1
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(target.suffix + ".tmp")
    temp.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(target)
    print(f"Collected stats for @{args.username}: {result['public_repositories']} public repositories")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
