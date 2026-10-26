import os
import re
import pytest
import yaml
from app.core.logging import get_request_id, set_request_id, RequestIdFilter, setup_logging
import logging

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_docker_compose_structure_and_healthchecks():
    """Verify docker-compose.yml defines all services with required healthchecks."""
    compose_path = os.path.join(PROJECT_ROOT, "docker-compose.yml")
    assert os.path.exists(compose_path), "docker-compose.yml must exist"

    with open(compose_path, "r", encoding="utf-8") as f:
        compose = yaml.safe_load(f)

    services = compose.get("services", {})
    assert "api" in services, "api service must be defined in docker-compose.yml"
    assert "mongo" in services, "mongo service must be defined in docker-compose.yml"
    assert "frontend" in services, "frontend service must be defined in docker-compose.yml"
    assert "redis" in services, "optional redis service must be defined in docker-compose.yml"

    # Verify healthchecks on all services
    for svc_name in ["api", "mongo", "frontend", "redis"]:
        assert "healthcheck" in services[svc_name], f"{svc_name} service must have healthcheck configured"
        assert "test" in services[svc_name]["healthcheck"], f"{svc_name} healthcheck must include test command"


def test_dockerfiles_exist():
    """Verify backend and frontend Dockerfiles exist and include healthchecks."""
    backend_dockerfile = os.path.join(PROJECT_ROOT, "backend", "Dockerfile")
    frontend_dockerfile = os.path.join(PROJECT_ROOT, "frontend", "Dockerfile")

    assert os.path.exists(backend_dockerfile), "backend/Dockerfile must exist"
    assert os.path.exists(frontend_dockerfile), "frontend/Dockerfile must exist"

    with open(backend_dockerfile, "r", encoding="utf-8") as f:
        backend_content = f.read()
        assert "HEALTHCHECK" in backend_content
        assert "uvicorn" in backend_content

    with open(frontend_dockerfile, "r", encoding="utf-8") as f:
        frontend_content = f.read()
        assert "FROM node" in frontend_content
        assert "FROM nginx" in frontend_content
        assert "HEALTHCHECK" in frontend_content


def test_request_id_structured_logging():
    """Verify structured logging attaches and formats request IDs."""
    set_request_id("test-req-999")
    assert get_request_id() == "test-req-999"

    filt = RequestIdFilter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Structured logging check",
        args=(),
        exc_info=None
    )
    res = filt.filter(record)
    assert res is True
    assert getattr(record, "request_id", None) == "test-req-999"


def test_git_lfs_and_model_download_script():
    """Verify Git LFS tracking configuration and model download helper script."""
    gitattributes_path = os.path.join(PROJECT_ROOT, ".gitattributes")
    assert os.path.exists(gitattributes_path)

    with open(gitattributes_path, "r", encoding="utf-8") as f:
        attrs = f.read()
        assert "*.joblib filter=lfs" in attrs

    download_script_path = os.path.join(PROJECT_ROOT, "backend", "scripts", "download_models.py")
    assert os.path.exists(download_script_path)

    with open(download_script_path, "r", encoding="utf-8") as f:
        script_content = f.read()
        assert "REQUIRED_MODELS" in script_content
        assert "is_lfs_pointer" in script_content


def test_env_examples_contain_all_required_keys():
    """Verify backend and frontend .env.example contain all mandatory settings."""
    backend_env_example = os.path.join(PROJECT_ROOT, "backend", ".env.example")
    frontend_env_example = os.path.join(PROJECT_ROOT, "frontend", ".env.example")

    assert os.path.exists(backend_env_example)
    assert os.path.exists(frontend_env_example)

    with open(backend_env_example, "r", encoding="utf-8") as f:
        backend_env = f.read()

    required_backend_vars = [
        "SECRET_KEY",
        "DEMO_MODE",
        "CORS_ORIGINS",
        "REDIS_URL",
        "LLM_PROVIDER",
        "LLM_API_KEY",
        "LLM_MODEL",
        "ANALYSIS_BACKEND",
        "STORAGE_BACKEND",
        "RESEND_API_KEY",
        "TWILIO_ACCOUNT_SID",
        "PLAN_FREE_MAX_BUSINESSES",
    ]
    for var in required_backend_vars:
        assert var in backend_env, f"backend/.env.example must document {var}"

    with open(frontend_env_example, "r", encoding="utf-8") as f:
        frontend_env = f.read()

    assert "VITE_API_URL" in frontend_env, "frontend/.env.example must document VITE_API_URL"


def test_changelog_and_readme_completeness():
    """Verify CHANGELOG.md and README.md reflect small business transformation."""
    changelog_path = os.path.join(PROJECT_ROOT, "CHANGELOG.md")
    readme_path = os.path.join(PROJECT_ROOT, "README.md")

    assert os.path.exists(changelog_path)
    assert os.path.exists(readme_path)

    with open(changelog_path, "r", encoding="utf-8") as f:
        changelog = f.read()

    assert "Breaking Changes" in changelog
    assert "Removed alias routes" in changelog or "Single Mount Prefix" in changelog
    assert "Client-Supplied Role Removed" in changelog
    assert "Token Security" in changelog or "Token Handling" in changelog
    assert "Renamed Concepts" in changelog or "Concept & Terminology Overhaul" in changelog

    with open(readme_path, "r", encoding="utf-8") as f:
        readme = f.read()

    assert "What are customers saying?" in readme
    assert "What is going wrong?" in readme
    assert "What should I do?" in readme
    assert "docker compose up" in readme
