"""Тесты для rendering/formatters.py"""
import pytest
from rendering.formatters import TypeFormatter, ExampleFormatter, DescriptionFormatter, StatsFormatter
from domain.models import Endpoint


@pytest.mark.unit
class TestTypeFormatter:
    """Тесты для TypeFormatter"""
    
    def test_format_simple_type(self):
        """Тест форматирования простого типа"""
        schema = {'type': 'string'}
        assert TypeFormatter.format(schema) == 'string'
    
    def test_format_ref(self):
        """Тест форматирования ссылки"""
        schema = {'$ref': '#/components/schemas/User'}
        assert TypeFormatter.format(schema) == '[User](#user)'
    
    def test_format_x_original_ref(self):
        """Тест форматирования сохраненной ссылки"""
        schema = {'x-original-ref': '#/components/schemas/User'}
        assert TypeFormatter.format(schema) == '[User](#user)'
    
    def test_format_array_primitive(self):
        """Тест форматирования массива примитивов"""
        schema = {'type': 'array', 'items': {'type': 'string'}}
        assert TypeFormatter.format(schema) == 'array<string>'
    
    def test_format_array_complex(self):
        """Тест форматирования массива сложных типов"""
        schema = {'type': 'array', 'items': {'$ref': '#/components/schemas/User'}}
        assert TypeFormatter.format(schema) == 'array<[User](#user)>'
    
    def test_format_object(self):
        """Тест форматирования объекта"""
        schema = {'type': 'object', 'properties': {'name': {'type': 'string'}}}
        assert TypeFormatter.format(schema) == 'object'
    
    def test_format_anyof(self):
        """Тест форматирования anyOf"""
        schema = {
            'anyOf': [
                {'type': 'string'},
                {'type': 'integer'}
            ]
        }
        result = TypeFormatter.format(schema)
        assert 'anyOf' in result
        assert 'string' in result
        assert 'integer' in result
    
    def test_format_oneof(self):
        """Тест форматирования oneOf"""
        schema = {
            'oneOf': [
                {'type': 'string'},
                {'type': 'integer'}
            ]
        }
        result = TypeFormatter.format(schema)
        assert 'oneOf' in result
    
    def test_format_allof(self):
        """Тест форматирования allOf"""
        schema = {
            'allOf': [
                {'type': 'string'},
                {'type': 'integer'}
            ]
        }
        result = TypeFormatter.format(schema)
        assert 'allOf' in result
    
    def test_format_additional_properties(self):
        """Тест форматирования additionalProperties"""
        schema = {
            'additionalProperties': {'type': 'string'}
        }
        assert TypeFormatter.format(schema) == 'object<string, string>'


@pytest.mark.unit
class TestExampleFormatter:
    """Тесты для ExampleFormatter"""
    
    def test_format_none(self):
        """Тест форматирования None"""
        assert ExampleFormatter.format(None) == ""
    
    def test_format_string(self):
        """Тест форматирования строки"""
        assert ExampleFormatter.format("test") == "test"
    
    def test_format_dict(self):
        """Тест форматирования словаря"""
        example = {'name': 'John', 'age': 30}
        result = ExampleFormatter.format(example)
        assert 'John' in result
        assert '30' in result
    
    def test_format_dict_truncated(self):
        """Тест обрезки длинного примера"""
        example = {'key': 'x' * 200}
        result = ExampleFormatter.format(example, max_length=50)
        assert len(result) <= 53  # 50 + "..."
        assert result.endswith("...")
    
    def test_extract_single_example(self):
        """Тест извлечения одиночного примера"""
        node = {'example': 'test_value'}
        examples = ExampleFormatter.extract(node)
        assert len(examples) == 1
        assert examples[0] == ('Пример', 'test_value')
    
    def test_extract_examples_dict(self):
        """Тест извлечения примеров из словаря"""
        node = {
            'examples': {
                'example1': {'value': 'value1', 'summary': 'Summary 1'},
                'example2': 'value2'
            }
        }
        examples = ExampleFormatter.extract(node)
        assert len(examples) == 2
    
    def test_extract_examples_list(self):
        """Тест извлечения примеров из списка"""
        node = {'examples': ['value1', 'value2']}
        examples = ExampleFormatter.extract(node)
        assert len(examples) == 2
        assert examples[0][0] == 'Пример 1'
    
    def test_extract_from_schema(self):
        """Тест извлечения примеров из схемы"""
        node = {
            'schema': {
                'example': 'schema_example',
                'examples': {'ex1': 'value1'}
            }
        }
        examples = ExampleFormatter.extract(node)
        assert len(examples) >= 1


@pytest.mark.unit
class TestDescriptionFormatter:
    """Тесты для DescriptionFormatter"""
    
    def test_format_description(self):
        """Тест форматирования описания"""
        node = {'description': 'Test description'}
        assert DescriptionFormatter.format(node) == 'Test description'
    
    def test_format_fallback_to_title(self):
        """Тест fallback на title"""
        node = {'title': 'Test title'}
        assert DescriptionFormatter.format(node) == 'Test title'
    
    def test_format_empty(self):
        """Тест пустого описания"""
        node = {}
        assert DescriptionFormatter.format(node) == ""
    
    def test_safe_replace_none(self):
        """Тест безопасной замены None"""
        assert DescriptionFormatter.safe_replace(None) == ""
    
    def test_safe_replace_newlines(self):
        """Тест замены переносов строк"""
        text = "Line 1\nLine 2"
        result = DescriptionFormatter.safe_replace(text)
        assert '<br>' in result
    
    def test_safe_replace_list_markers(self):
        """Тест замены маркеров списка"""
        text = "Item 1  - Item 2"
        result = DescriptionFormatter.safe_replace(text)
        assert '<br>- ' in result


@pytest.mark.unit
class TestStatsFormatter:
    """Тесты для StatsFormatter"""
    
    def test_calculate_stats_empty(self):
        """Тест вычисления статистики для пустого списка"""
        stats = StatsFormatter.calculate_stats([])
        assert stats['total'] == 0
        assert stats['unique_paths'] == 0
        assert stats['with_summary'] == 0
        assert stats['summary_percent'] == 0
    
    def test_calculate_stats_basic(self):
        """Тест базовой статистики"""
        endpoints = [
            Endpoint(
                path="/api/v1/users",
                method="GET",
                operation={"summary": "Get users", "tags": ["users"]},
                tags=["users"]
            ),
            Endpoint(
                path="/api/v1/users",
                method="POST",
                operation={"summary": "Create user", "tags": ["users"]},
                tags=["users"]
            ),
            Endpoint(
                path="/api/v1/posts",
                method="GET",
                operation={"tags": ["posts"]},
                tags=["posts"]
            ),
        ]
        stats = StatsFormatter.calculate_stats(endpoints)
        assert stats['total'] == 3
        assert stats['unique_paths'] == 2
        assert stats['with_summary'] == 2
        assert stats['summary_percent'] == pytest.approx(66.67, rel=0.01)
        assert stats['without_tags'] == 0
        assert stats['methods']['GET'] == 2
        assert stats['methods']['POST'] == 1
    
    def test_calculate_stats_without_tags(self):
        """Тест статистики для эндпоинтов без тегов"""
        endpoints = [
            Endpoint(
                path="/api/v1/test",
                method="GET",
                operation={},
                tags=[]
            ),
        ]
        stats = StatsFormatter.calculate_stats(endpoints)
        assert stats['without_tags'] == 1
        assert stats['without_tags_percent'] == 100.0
        assert 'Без тега' in stats['tags']
        assert stats['tags']['Без тега'] == 1
    
    def test_calculate_stats_deprecated(self):
        """Тест статистики для deprecated эндпоинтов"""
        endpoints = [
            Endpoint(
                path="/api/v1/old",
                method="GET",
                operation={"deprecated": True},
                tags=["old"]
            ),
            Endpoint(
                path="/api/v1/new",
                method="GET",
                operation={},
                tags=["new"]
            ),
        ]
        stats = StatsFormatter.calculate_stats(endpoints)
        assert stats['deprecated'] == 1
        assert stats['deprecated_percent'] == 50.0
    
    def test_calculate_stats_versions(self):
        """Тест статистики по версиям API"""
        endpoints = [
            Endpoint(path="/api/v1/users", method="GET", operation={}, tags=[]),
            Endpoint(path="/api/v1/posts", method="GET", operation={}, tags=[]),
            Endpoint(path="/api/v2/users", method="GET", operation={}, tags=[]),
            Endpoint(path="/other/path", method="GET", operation={}, tags=[]),
        ]
        stats = StatsFormatter.calculate_stats(endpoints)
        assert stats['versions']['v1'] == 2
        assert stats['versions']['v2'] == 1
        assert stats['versions']['без версии'] == 1
    
    def test_extract_version_v1(self):
        """Тест извлечения версии v1"""
        assert StatsFormatter._extract_version("/api/v1/users") == "v1"
    
    def test_extract_version_v2(self):
        """Тест извлечения версии v2"""
        assert StatsFormatter._extract_version("/api/v2/posts") == "v2"
    
    def test_extract_version_without_api(self):
        """Тест извлечения версии без /api/"""
        assert StatsFormatter._extract_version("/v1/users") == "v1"
    
    def test_extract_version_no_version(self):
        """Тест извлечения версии когда её нет"""
        assert StatsFormatter._extract_version("/users") == "без версии"
        assert StatsFormatter._extract_version("/other/path") == "без версии"
    
    def test_format_stats(self):
        """Тест форматирования статистики"""
        endpoints = [
            Endpoint(
                path="/api/v1/users",
                method="GET",
                operation={"summary": "Get users", "tags": ["users"]},
                tags=["users"]
            ),
        ]
        stats = StatsFormatter.calculate_stats(endpoints)
        formatted = StatsFormatter.format(stats)
        
        assert "📊 Статистика API" in formatted
        assert "Всего эндпоинтов: 1" in formatted
        assert "GET" in formatted
        assert "v1" in formatted
        assert "users" in formatted
    
    def test_format_stats_empty(self):
        """Тест форматирования пустой статистики"""
        stats = StatsFormatter.calculate_stats([])
        formatted = StatsFormatter.format(stats)
        
        assert "📊 Статистика API" in formatted
        assert "Всего эндпоинтов: 0" in formatted

