# ABOUTME: Tests that static assets include cache-busting query parameters.
# ABOUTME: Validates that HTML responses contain versioned ?v= hashes on script/link tags.
"""
Tests for Issue #38: Static JS/CSS assets must include cache-busting hashes.

Templates must append ?v=<content_hash> to static asset URLs so that
browser caches are invalidated when files change.
"""

import hashlib
import re
import pytest
from pathlib import Path


class TestCacheBustingInTemplates:
    """Verify that rendered pages include cache-busting query strings."""

    def test_dashboard_scripts_have_version_param(self, isolated_app_client):
        """Dashboard page script tags must include ?v= query parameter."""
        response = isolated_app_client.get("/")
        assert response.status_code == 200
        html = response.text
        # Find all local script src attributes
        script_srcs = re.findall(r'<script\s+src="(/static/[^"]+)"', html)
        assert len(script_srcs) > 0, "Expected at least one local script tag"
        for src in script_srcs:
            assert "?v=" in src, f"Script {src} missing cache-busting ?v= parameter"

    def test_dashboard_stylesheets_have_version_param(self, isolated_app_client):
        """Dashboard page link tags must include ?v= query parameter."""
        response = isolated_app_client.get("/")
        assert response.status_code == 200
        html = response.text
        link_hrefs = re.findall(r'<link\s+rel="stylesheet"\s+href="(/static/[^"]+)"', html)
        assert len(link_hrefs) > 0, "Expected at least one local stylesheet link"
        for href in link_hrefs:
            assert "?v=" in href, f"Stylesheet {href} missing cache-busting ?v= parameter"

    def test_version_hash_matches_file_content(self, isolated_app_client):
        """The ?v= hash must correspond to the actual file content."""
        response = isolated_app_client.get("/")
        html = response.text
        # Extract a script src with its hash
        match = re.search(r'<script\s+src="/static/([^?]+)\?v=([a-f0-9]+)"', html)
        assert match, "No versioned script tag found"
        file_rel_path, url_hash = match.group(1), match.group(2)
        # Compute expected hash from actual file
        static_dir = Path(__file__).parent.parent / "web" / "static"
        file_path = static_dir / file_rel_path
        assert file_path.exists(), f"Static file {file_path} not found"
        content_hash = hashlib.md5(file_path.read_bytes()).hexdigest()[:10]
        assert url_hash == content_hash, \
            f"URL hash {url_hash} doesn't match content hash {content_hash} for {file_rel_path}"

    def test_calendar_page_has_versioned_assets(self, isolated_app_client):
        """Calendar page must also have versioned assets."""
        response = isolated_app_client.get("/calendar")
        assert response.status_code == 200
        html = response.text
        script_srcs = re.findall(r'<script\s+src="(/static/[^"]+)"', html)
        for src in script_srcs:
            assert "?v=" in src, f"Script {src} missing cache-busting ?v= parameter"

    def test_cdn_scripts_not_affected(self, isolated_app_client):
        """CDN scripts (https://) should not have ?v= added."""
        response = isolated_app_client.get("/entry/2026-01-01")
        html = response.text
        cdn_srcs = re.findall(r'<script\s+src="(https://[^"]+)"', html)
        for src in cdn_srcs:
            # CDN scripts already have their own versioning
            assert "?v=" not in src or "integrity" in html, \
                f"CDN script should not use our cache-busting: {src}"
