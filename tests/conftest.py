"""Конфигурация и фикстуры для pytest"""
import json
import pytest
from pathlib import Path
from typing import Dict, Set, Tuple


@pytest.fixture
def fixtures_dir():
    """Возвращает путь к директории с фикстурами"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_openapi_spec(fixtures_dir) -> Dict:
    """Загружает sample_openapi.json"""
    spec_path = fixtures_dir / "sample_openapi.json"
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def minimal_openapi_spec(fixtures_dir) -> Dict:
    """Загружает minimal_openapi.json"""
    spec_path = fixtures_dir / "minimal_openapi.json"
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def sample_spec_path(fixtures_dir, tmp_path) -> str:
    """Создает временный файл с sample_openapi.json и возвращает путь"""
    spec_path = fixtures_dir / "sample_openapi.json"
    temp_spec = tmp_path / "openapi.json"
    temp_spec.write_text(spec_path.read_text(encoding='utf-8'), encoding='utf-8')
    return str(temp_spec)


@pytest.fixture
def minimal_spec_path(fixtures_dir, tmp_path) -> str:
    """Создает временный файл с minimal_openapi.json и возвращает путь"""
    spec_path = fixtures_dir / "minimal_openapi.json"
    temp_spec = tmp_path / "openapi.json"
    temp_spec.write_text(spec_path.read_text(encoding='utf-8'), encoding='utf-8')
    return str(temp_spec)


@pytest.fixture
def clear_resolve_ref_cache():
    """Очищает кеш функции resolve_ref перед тестом (legacy, больше не используется)"""
    # Старая функция resolve_ref больше не используется
    yield


@pytest.fixture
def endpoints_filter_file(tmp_path) -> str:
    """Создает временный файл с фильтром эндпоинтов"""
    filter_file = tmp_path / "endpoints.txt"
    filter_file.write_text(
        "GET /api/v1/users\n"
        "POST /api/v1/posts\n"
        "PUT /api/v1/users/{id}\n",
        encoding='utf-8'
    )
    return str(filter_file)


@pytest.fixture
def endpoints_filter_with_comments(tmp_path) -> str:
    """Создает временный файл с фильтром эндпоинтов и комментариями"""
    filter_file = tmp_path / "endpoints.txt"
    filter_file.write_text(
        "# Комментарий\n"
        "GET /api/v1/users\n"
        "# Еще комментарий\n"
        "POST /api/v1/posts\n"
        "\n"
        "PUT /api/v1/users/{id}\n",
        encoding='utf-8'
    )
    return str(filter_file)


@pytest.fixture
def endpoints_filter_invalid_format(tmp_path) -> str:
    """Создает временный файл с некорректным форматом"""
    filter_file = tmp_path / "endpoints.txt"
    filter_file.write_text(
        "GET /api/v1/users\n"
        "invalid_line\n"
        "POST /api/v1/posts\n",
        encoding='utf-8'
    )
    return str(filter_file)


@pytest.fixture
def expected_endpoints_filter() -> Set[Tuple[str, str]]:
    """Возвращает ожидаемый набор эндпоинтов для фильтра"""
    return {
        ("GET", "/api/v1/users"),
        ("POST", "/api/v1/posts"),
        ("PUT", "/api/v1/users/{id}")
    }


@pytest.fixture
def spec_with_recursive_refs() -> Dict:
    """Создает спецификацию с рекурсивными ссылками для тестирования"""
    return {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "role": {"$ref": "#/components/schemas/UserRole"}
                    }
                },
                "UserRole": {
                    "type": "string",
                    "enum": ["admin", "user"]
                },
                "Nested": {
                    "$ref": "#/components/schemas/User"
                }
            }
        }
    }


@pytest.fixture
def spec_with_parameters() -> Dict:
    """Создает спецификацию с параметрами для тестирования"""
    return {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {},
        "components": {
            "parameters": {
                "LimitParam": {
                    "name": "limit",
                    "in": "query",
                    "schema": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100
                    }
                }
            },
            "schemas": {}
        }
    }


@pytest.fixture
def schema_with_ref() -> Dict:
    """Создает схему со ссылкой для тестирования"""
    return {
        "$ref": "#/components/schemas/User",
        "description": "Test description"
    }


@pytest.fixture
def schema_with_nested_refs() -> Dict:
    """Создает схему с вложенными ссылками"""
    return {
        "type": "object",
        "properties": {
            "user": {
                "$ref": "#/components/schemas/User"
            },
            "role": {
                "$ref": "#/components/schemas/UserRole"
            },
            "metadata": {
                "type": "object",
                "properties": {
                    "count": {"type": "integer"}
                }
            }
        }
    }


@pytest.fixture
def schema_array_with_ref() -> Dict:
    """Создает схему массива со ссылкой"""
    return {
        "type": "array",
        "items": {
            "$ref": "#/components/schemas/User"
        }
    }


@pytest.fixture(autouse=True)
def reset_resolve_ref_cache():
    """Автоматически очищает кеш resolve_ref перед каждым тестом (legacy, больше не используется)"""
    # Старая функция resolve_ref больше не используется
    yield

