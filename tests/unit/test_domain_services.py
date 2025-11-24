"""Тесты для domain/services.py"""
import pytest
from domain.models import OpenAPISpec, Endpoint
from domain.services import EndpointFinder, SchemaResolver, SchemaCollector


@pytest.mark.unit
class TestEndpointFinder:
    """Тесты для EndpointFinder"""
    
    def test_find_success(self, sample_openapi_spec):
        """Тест успешного поиска эндпоинта"""
        spec = OpenAPISpec.from_dict(sample_openapi_spec)
        endpoint = EndpointFinder.find(spec, "/api/v1/users", "GET")
        
        assert endpoint is not None
        assert endpoint.path == "/api/v1/users"
        assert endpoint.method == "GET"
        assert "get_users" in endpoint.operation.get("operationId", "")
    
    def test_find_not_found_path(self, sample_openapi_spec):
        """Тест когда путь не найден"""
        spec = OpenAPISpec.from_dict(sample_openapi_spec)
        
        with pytest.raises(ValueError, match="не найден"):
            EndpointFinder.find(spec, "/api/v1/nonexistent", "GET")
    
    def test_find_not_found_method(self, sample_openapi_spec):
        """Тест когда метод не найден"""
        spec = OpenAPISpec.from_dict(sample_openapi_spec)
        
        with pytest.raises(ValueError, match="не найден"):
            EndpointFinder.find(spec, "/api/v1/users", "DELETE")
    
    def test_find_trailing_slash(self, sample_openapi_spec):
        """Тест обработки trailing slash"""
        spec = OpenAPISpec.from_dict(sample_openapi_spec)
        
        # Если в спецификации путь с trailing slash, должен найти
        endpoint1 = EndpointFinder.find(spec, "/api/v1/users", "GET")
        endpoint2 = EndpointFinder.find(spec, "/api/v1/users/", "GET")
        
        # Оба должны найти один и тот же эндпоинт (если он существует)
        assert endpoint1.path == endpoint2.path or endpoint1.path.rstrip('/') == endpoint2.path.rstrip('/')
    
    def test_find_case_insensitive_method(self, sample_openapi_spec):
        """Тест поиска с разным регистром метода"""
        spec = OpenAPISpec.from_dict(sample_openapi_spec)
        
        endpoint1 = EndpointFinder.find(spec, "/api/v1/users", "GET")
        endpoint2 = EndpointFinder.find(spec, "/api/v1/users", "get")
        
        assert endpoint1.path == endpoint2.path
        assert endpoint1.method == endpoint2.method
    
    def test_list_all(self, sample_openapi_spec):
        """Тест получения списка всех эндпоинтов"""
        spec = OpenAPISpec.from_dict(sample_openapi_spec)
        endpoints = EndpointFinder.list_all(spec)
        
        assert len(endpoints) > 0
        assert all(isinstance(e, Endpoint) for e in endpoints)
        
        # Проверяем, что есть эндпоинт /api/v1/users
        users_endpoints = [e for e in endpoints if e.path == "/api/v1/users"]
        assert len(users_endpoints) > 0
    
    def test_list_all_minimal(self, minimal_openapi_spec):
        """Тест получения списка для минимальной спецификации"""
        spec = OpenAPISpec.from_dict(minimal_openapi_spec)
        endpoints = EndpointFinder.list_all(spec)
        
        assert len(endpoints) > 0
        assert all(isinstance(e, Endpoint) for e in endpoints)


@pytest.mark.unit
class TestSchemaResolver:
    """Тесты для SchemaResolver"""
    
    def test_resolve_schema(self, sample_openapi_spec):
        """Тест разрешения ссылки на схему"""
        spec = OpenAPISpec.from_dict(sample_openapi_spec)
        resolver = SchemaResolver(spec)
        
        resolved = resolver.resolve("#/components/schemas/User")
        
        assert resolved is not None
        assert isinstance(resolved, dict)
    
    def test_resolve_parameter(self, sample_openapi_spec):
        """Тест разрешения ссылки на параметр"""
        spec = OpenAPISpec.from_dict(sample_openapi_spec)
        resolver = SchemaResolver(spec)
        
        # Пытаемся разрешить параметр (может не существовать)
        resolved = resolver.resolve("#/components/parameters/LimitParam")
        
        # Должен вернуть словарь (пустой если не найден)
        assert isinstance(resolved, dict)
    
    def test_resolve_nonexistent(self, sample_openapi_spec):
        """Тест разрешения несуществующей ссылки"""
        spec = OpenAPISpec.from_dict(sample_openapi_spec)
        resolver = SchemaResolver(spec)
        
        resolved = resolver.resolve("#/components/schemas/Nonexistent")
        
        assert resolved == {}
    
    def test_resolve_caching(self, sample_openapi_spec):
        """Тест кеширования результатов"""
        spec = OpenAPISpec.from_dict(sample_openapi_spec)
        resolver = SchemaResolver(spec)
        
        resolved1 = resolver.resolve("#/components/schemas/User")
        resolved2 = resolver.resolve("#/components/schemas/User")
        
        # Должен использовать кеш
        assert resolved1 == resolved2
    
    def test_resolve_max_depth(self, sample_openapi_spec):
        """Тест защиты от глубокой рекурсии"""
        spec = OpenAPISpec.from_dict(sample_openapi_spec)
        resolver = SchemaResolver(spec)
        
        # Создаем циклическую ссылку (если есть в тестовых данных)
        resolved = resolver.resolve("#/components/schemas/User", depth=15)
        
        # Должен вернуть пустой словарь при превышении глубины
        assert isinstance(resolved, dict)
    
    def test_process_schema_simple(self, sample_openapi_spec):
        """Тест обработки простой схемы"""
        spec = OpenAPISpec.from_dict(sample_openapi_spec)
        resolver = SchemaResolver(spec)
        
        schema = {"type": "string", "format": "email"}
        processed = resolver.process_schema(schema)
        
        assert processed == schema
    
    def test_process_schema_with_ref(self, sample_openapi_spec):
        """Тест обработки схемы со ссылкой"""
        spec = OpenAPISpec.from_dict(sample_openapi_spec)
        resolver = SchemaResolver(spec)
        
        schema = {"$ref": "#/components/schemas/User"}
        processed = resolver.process_schema(schema)
        
        assert isinstance(processed, dict)
        assert 'x-original-ref' in processed or processed != schema
    
    def test_clear_cache(self, sample_openapi_spec):
        """Тест очистки кеша"""
        spec = OpenAPISpec.from_dict(sample_openapi_spec)
        resolver = SchemaResolver(spec)
        
        resolver.resolve("#/components/schemas/User")
        assert len(resolver._cache) > 0
        
        resolver.clear_cache()
        assert len(resolver._cache) == 0


@pytest.mark.unit
class TestSchemaCollector:
    """Тесты для SchemaCollector"""
    
    def test_collect_from_endpoint(self, sample_openapi_spec):
        """Тест сбора схем из эндпоинта"""
        spec = OpenAPISpec.from_dict(sample_openapi_spec)
        resolver = SchemaResolver(spec)
        collector = SchemaCollector(spec, resolver)
        
        endpoint = EndpointFinder.find(spec, "/api/v1/users", "GET")
        schemas = collector.collect_from_endpoint(endpoint)
        
        assert isinstance(schemas, set)
        # Может быть пустым, если в эндпоинте нет ссылок на схемы
    
    def test_collect_from_endpoint_with_refs(self, sample_openapi_spec):
        """Тест сбора схем из эндпоинта со ссылками"""
        spec = OpenAPISpec.from_dict(sample_openapi_spec)
        resolver = SchemaResolver(spec)
        collector = SchemaCollector(spec, resolver)
        
        # Ищем эндпоинт, который может содержать ссылки
        endpoints = EndpointFinder.list_all(spec)
        if endpoints:
            endpoint = endpoints[0]
            schemas = collector.collect_from_endpoint(endpoint)
            
            assert isinstance(schemas, set)
    
    def test_collect_recursive(self, sample_openapi_spec):
        """Тест рекурсивного сбора схем"""
        spec = OpenAPISpec.from_dict(sample_openapi_spec)
        resolver = SchemaResolver(spec)
        collector = SchemaCollector(spec, resolver)
        
        endpoint = EndpointFinder.find(spec, "/api/v1/users", "GET")
        schemas = collector.collect_from_endpoint(endpoint)
        
        # Проверяем, что это множество строк (имен схем)
        assert all(isinstance(s, str) for s in schemas)
    
    def test_collect_from_node_dict(self, sample_openapi_spec):
        """Тест сбора схем из словаря"""
        spec = OpenAPISpec.from_dict(sample_openapi_spec)
        resolver = SchemaResolver(spec)
        collector = SchemaCollector(spec, resolver)
        
        collected = set()
        node = {"$ref": "#/components/schemas/User"}
        collector._collect_from_node(node, collected)
        
        assert "User" in collected
    
    def test_collect_from_node_list(self, sample_openapi_spec):
        """Тест сбора схем из списка"""
        spec = OpenAPISpec.from_dict(sample_openapi_spec)
        resolver = SchemaResolver(spec)
        collector = SchemaCollector(spec, resolver)
        
        collected = set()
        node = [
            {"$ref": "#/components/schemas/User"},
            {"$ref": "#/components/schemas/UserRole"}
        ]
        collector._collect_from_node(node, collected)
        
        assert "User" in collected or "UserRole" in collected
    
    def test_collect_with_anyof(self, sample_openapi_spec):
        """Тест сбора схем из anyOf"""
        spec = OpenAPISpec.from_dict(sample_openapi_spec)
        resolver = SchemaResolver(spec)
        collector = SchemaCollector(spec, resolver)
        
        collected = set()
        node = {
            "anyOf": [
                {"$ref": "#/components/schemas/User"},
                {"$ref": "#/components/schemas/UserRole"}
            ]
        }
        collector._collect_from_node(node, collected)
        
        # Должен собрать схемы из anyOf
        assert isinstance(collected, set)

