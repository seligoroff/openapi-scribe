"""Тест для проверки настройки тестового окружения"""
import pytest
from pathlib import Path


@pytest.mark.unit
def test_fixtures_dir_exists(fixtures_dir):
    """Проверяет, что директория с фикстурами существует"""
    assert fixtures_dir.exists()
    assert fixtures_dir.is_dir()


@pytest.mark.unit
def test_minimal_openapi_spec_exists(fixtures_dir):
    """Проверяет, что minimal_openapi.json существует"""
    spec_path = fixtures_dir / "minimal_openapi.json"
    assert spec_path.exists()


@pytest.mark.unit
def test_sample_openapi_spec_exists(fixtures_dir):
    """Проверяет, что sample_openapi.json существует"""
    spec_path = fixtures_dir / "sample_openapi.json"
    assert spec_path.exists()


@pytest.mark.unit
def test_minimal_openapi_spec_structure(minimal_openapi_spec):
    """Проверяет структуру minimal_openapi.json"""
    assert "openapi" in minimal_openapi_spec
    assert "info" in minimal_openapi_spec
    assert "paths" in minimal_openapi_spec
    assert minimal_openapi_spec["openapi"] == "3.0.0"


@pytest.mark.unit
def test_sample_openapi_spec_structure(sample_openapi_spec):
    """Проверяет структуру sample_openapi.json"""
    assert "openapi" in sample_openapi_spec
    assert "info" in sample_openapi_spec
    assert "paths" in sample_openapi_spec
    assert "components" in sample_openapi_spec
    assert sample_openapi_spec["openapi"] == "3.0.0"


@pytest.mark.unit
def test_sample_spec_path_fixture(sample_spec_path):
    """Проверяет фикстуру sample_spec_path"""
    assert Path(sample_spec_path).exists()
    assert Path(sample_spec_path).suffix == ".json"


@pytest.mark.unit
def test_minimal_spec_path_fixture(minimal_spec_path):
    """Проверяет фикстуру minimal_spec_path"""
    assert Path(minimal_spec_path).exists()
    assert Path(minimal_spec_path).suffix == ".json"

