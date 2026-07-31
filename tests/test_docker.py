import os
import pytest
from pathlib import Path


def test_dockerfile_exists_and_valid():
    root_dir = Path(__file__).parent.parent
    dockerfile_path = root_dir / "Dockerfile"
    assert dockerfile_path.exists()

    content = dockerfile_path.read_text(encoding="utf-8")
    assert "FROM" in content
    assert "uv" in content
    assert "EXPOSE 8501" in content
    assert "streamlit" in content
    assert "app.py" in content


def test_docker_compose_exists_and_valid():
    root_dir = Path(__file__).parent.parent
    compose_path = root_dir / "docker-compose.yml"
    assert compose_path.exists()

    content = compose_path.read_text(encoding="utf-8")
    assert "services:" in content
    assert "ai-consilium" in content
    assert "8501:8501" in content
    assert "env_file" in content
    assert "volumes:" in content
