from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List

from github import Github


COOKIE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"session(_id)?",
        r"auth(_token)?",
        r"jwt",
        r"csrf",
        r"remember_me",
        r"access(_token)?",
        r"refresh(_token)?",
    ]
]


@dataclass
class RepoCandidate:
    name: str
    url: str
    confidence: float


class DiscoveryEngine:
    def __init__(self, token: str, org: str) -> None:
        self.client = Github(token)
        self.org = org

    def discover(self) -> List[RepoCandidate]:
        org = self.client.get_organization(self.org)
        candidates: List[RepoCandidate] = []
        for repo in org.get_repos():
            confidence = self._score_repo(repo)
            if confidence > 0:
                candidates.append(RepoCandidate(name=repo.full_name, url=repo.html_url, confidence=confidence))
        return sorted(candidates, key=lambda c: c.confidence, reverse=True)

    def _score_repo(self, repo: object) -> float:
        score = 0.0
        contents = repo.get_contents("/")
        for item in contents:
            if item.type == "file" and item.name.endswith((".env", ".yaml", ".yml", ".json", ".py", ".js")):
                score += 0.1
        score += min(repo.stargazers_count / 1000, 0.5)
        return min(score, 1.0)


def score_cookie_names(names: Iterable[str]) -> float:
    hits = 0
    total = 0
    for name in names:
        total += 1
        if any(pattern.search(name) for pattern in COOKIE_PATTERNS):
            hits += 1
    if total == 0:
        return 0.0
    return min(1.0, hits / total + 0.1)
