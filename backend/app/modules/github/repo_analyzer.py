"""GitHub Public Repository & Secret Leakage Intelligence Module for APEX OSINT."""

import re
from datetime import datetime
from typing import Dict, Any, List
from app.config import settings
from app.core.security import SafeHTTPClient, redact_secrets
from app.modules.base import (
    BaseOSINTModule,
    NormalizedFinding,
    NormalizedEntity,
    NormalizedEvidence,
    NormalizedRelationship,
    NormalizedTimelineEvent,
)


class GitHubRepoAnalyzerModule(BaseOSINTModule):
    name = "github_repo_analyzer"
    display_name = "GitHub Public Code Intelligence"
    description = "Analyzes public GitHub repositories, contributors, commit authors, and scans for potential credential exposures."
    category = "GITHUB"
    target_types = ["REPOSITORY", "USERNAME"]
    rate_limit = 2.0
    source = "GitHub Public API"

    async def collect(self, target_value: str, target_type: str, context: Dict[str, Any]) -> NormalizedFinding:
        finding = NormalizedFinding()
        client = SafeHTTPClient(timeout=8.0)
        headers = {"Accept": "application/vnd.github.v3+json"}
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"

        # If target is REPOSITORY e.g. "owner/repo" or "https://github.com/owner/repo"
        repo_path = target_value.replace("https://github.com/", "").strip("/")
        if "/" not in repo_path:
            # If target is single username, query their public repos
            user_url = f"https://api.github.com/users/{repo_path}/repos?sort=updated&per_page=5"
            try:
                resp = await client.get(user_url, headers=headers)
                if resp.status_code == 200:
                    repos = resp.json()
                    for r in repos:
                        r_name = r.get("full_name")
                        finding.discovered_entities.append(
                            NormalizedEntity(
                                type="REPOSITORY",
                                value=r_name,
                                normalized_value=r_name.lower(),
                                confidence=0.95,
                                metadata={"stars": r.get("stargazers_count"), "language": r.get("language")}
                            )
                        )
                        finding.relationships.append(
                            NormalizedRelationship(
                                source_value=repo_path,
                                source_type="USERNAME",
                                target_value=r_name,
                                target_type="REPOSITORY",
                                relation_type="AUTHORED",
                                confidence=0.95
                            )
                        )
            except Exception:
                pass
            return finding

        # Analyze Repository
        repo_url = f"https://api.github.com/repos/{repo_path}"
        try:
            repo_resp = await client.get(repo_url, headers=headers)
            if repo_resp.status_code != 200:
                return finding
            repo_data = repo_resp.json()
        except Exception:
            return finding

        owner = repo_data.get("owner", {}).get("login", "")
        repo_name = repo_data.get("full_name", repo_path)
        description = repo_data.get("description") or ""
        stars = repo_data.get("stargazers_count", 0)
        language = repo_data.get("language")
        created_at_str = repo_data.get("created_at")

        finding.primary_entity = NormalizedEntity(
            type="REPOSITORY",
            value=repo_name,
            normalized_value=repo_name.lower(),
            confidence=1.0,
            metadata={"stars": stars, "language": language, "description": description}
        )

        evidence_snippet = f"GitHub repository {repo_name} analyzed: {stars} stars, primary language {language or 'Unknown'}, owned by {owner}."
        finding.evidence.append(
            NormalizedEvidence(
                source_name="GitHub Public REST API",
                source_type="CODE_REPOSITORY",
                source_url=f"https://github.com/{repo_path}",
                snippet=evidence_snippet,
                collection_method="GITHUB_REST_API",
                confidence=0.99,
                epistemic_label="OBSERVED",
                raw_payload={"repo": repo_name, "owner": owner, "stars": stars, "license": repo_data.get("license")},
                related_entity_values=[repo_name, owner]
            )
        )

        # Timeline event for repository creation
        if created_at_str:
            try:
                dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                finding.timeline_events.append(
                    NormalizedTimelineEvent(
                        timestamp=dt,
                        event_type="REPOSITORY_CREATED",
                        title=f"GitHub Repository {repo_name} Created",
                        description=f"Public repository created by {owner}.",
                        entity_value=repo_name,
                        confidence=0.99
                    )
                )
            except Exception:
                pass

        # Connect Owner Entity
        if owner:
            finding.discovered_entities.append(
                NormalizedEntity(
                    type="USERNAME",
                    value=owner,
                    normalized_value=owner.lower(),
                    confidence=0.98,
                    metadata={"role": "repository_owner"}
                )
            )
            finding.relationships.append(
                NormalizedRelationship(
                    source_value=owner,
                    source_type="USERNAME",
                    target_value=repo_name,
                    target_type="REPOSITORY",
                    relation_type="OWNS",
                    confidence=0.98,
                    evidence_indices=[0]
                )
            )

        # Fetch Contributors / Recent Commits
        commits_url = f"https://api.github.com/repos/{repo_path}/commits?per_page=5"
        try:
            commits_resp = await client.get(commits_url, headers=headers)
            if commits_resp.status_code == 200:
                commits = commits_resp.json()
                for c in commits:
                    commit_author = c.get("commit", {}).get("author", {})
                    author_name = commit_author.get("name")
                    author_email = commit_author.get("email")
                    commit_msg = c.get("commit", {}).get("message", "")

                    # Check for accidental secret leakage in commit messages
                    sanitized_msg, secret_found = redact_secrets(commit_msg)
                    if secret_found:
                        finding.evidence.append(
                            NormalizedEvidence(
                                source_name="GitHub Commit Message Scanner",
                                source_type="CODE_REPOSITORY",
                                source_url=c.get("html_url"),
                                snippet=f"POTENTIAL SECRET EXPOSURE detected in commit: {sanitized_msg[:120]}...",
                                collection_method="COMMIT_AUDIT",
                                confidence=0.85,
                                epistemic_label="OBSERVED",
                                raw_payload={"commit_sha": c.get("sha"), "message_preview": sanitized_msg[:200]}
                            )
                        )

                    if author_email and not author_email.endswith("users.noreply.github.com"):
                        clean_email = author_email.lower().strip()
                        finding.discovered_entities.append(
                            NormalizedEntity(
                                type="EMAIL",
                                value=clean_email,
                                normalized_value=clean_email,
                                confidence=0.92,
                                metadata={"role": "git_commit_author", "author_name": author_name}
                            )
                        )
                        finding.relationships.append(
                            NormalizedRelationship(
                                source_value=clean_email,
                                source_type="EMAIL",
                                target_value=repo_name,
                                target_type="REPOSITORY",
                                relation_type="CONTRIBUTES_TO",
                                confidence=0.92,
                                evidence_indices=[0]
                            )
                        )
        except Exception:
            pass

        return finding
