# ABOUTME: Tests for Docker configuration files existence and required content.
# ABOUTME: Validates Dockerfile and docker-compose files have necessary instructions.
"""Tests for Docker configuration files."""
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


class TestDockerFiles:
    def test_dockerfile_exists(self):
        assert (PROJECT_ROOT / "Dockerfile").exists()

    def test_dockerfile_has_required_instructions(self):
        content = (PROJECT_ROOT / "Dockerfile").read_text()
        assert "FROM python:" in content
        assert "EXPOSE" in content
        assert "CMD" in content or "ENTRYPOINT" in content

    def test_docker_compose_exists(self):
        assert (PROJECT_ROOT / "docker-compose.yml").exists()

    def test_docker_compose_server_exists(self):
        assert (PROJECT_ROOT / "docker-compose.server.yml").exists()
