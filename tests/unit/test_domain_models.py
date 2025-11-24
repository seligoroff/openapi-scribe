"""Тесты для domain/models.py"""
import pytest
from domain.models import OpenAPISpec, Endpoint, Schema, EndpointFilter


@pytest.mark.unit
class TestOpenAPISpec:
    """Тесты для OpenAPISpec"""
    
    def test_from_dict(self, sample_openapi_spec):
        """Тест создания OpenAPISpec из словаря"""
        spec = OpenAPISpec.from_dict(sample_openapi_spec)
        
        assert isinstance(spec, OpenAPISpec)
        assert spec.raw == sample_openapi_spec
        assert spec.paths == sample_openapi_spec['paths']
        assert spec.schemas == sample_openapi_spec['components']['schemas']
        assert spec.info == sample_openapi_spec['info']
    
    def test_from_dict_empty_paths(self):
        """Тест создания OpenAPISpec с пустыми paths"""
        spec_dict = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {},
            "components": {"schemas": {}}
        }
        spec = OpenAPISpec.from_dict(spec_dict)
        
        assert spec.paths == {}
        assert spec.schemas == {}
    
    def test_from_dict_no_components(self):
        """Тест создания OpenAPISpec без components"""
        spec_dict = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {}
        }
        spec = OpenAPISpec.from_dict(spec_dict)
        
        assert spec.schemas == {}
    
    def test_immutability(self, sample_openapi_spec):
        """Тест неизменяемости OpenAPISpec"""
        spec = OpenAPISpec.from_dict(sample_openapi_spec)
        
        with pytest.raises(Exception):
            spec.paths = {}


@pytest.mark.unit
class TestEndpoint:
    """Тесты для Endpoint"""
    
    def test_endpoint_creation(self):
        """Тест создания Endpoint"""
        operation = {
            "tags": ["users"],
            "summary": "Get users",
            "operationId": "get_users"
        }
        endpoint = Endpoint(
            path="/api/v1/users",
            method="get",
            operation=operation,
            tags=["users"]
        )
        
        assert endpoint.path == "/api/v1/users"
        assert endpoint.method == "GET"  # Должен быть в верхнем регистре
        assert endpoint.operation == operation
        assert endpoint.tags == ["users"]
    
    def test_method_normalization(self):
        """Тест нормализации метода к верхнему регистру"""
        operation = {"tags": ["test"]}
        endpoint = Endpoint(
            path="/test",
            method="post",
            operation=operation,
            tags=["test"]
        )
        
        assert endpoint.method == "POST"
    
    def test_immutability(self):
        """Тест неизменяемости Endpoint"""
        operation = {"tags": ["test"]}
        endpoint = Endpoint(
            path="/test",
            method="GET",
            operation=operation,
            tags=["test"]
        )
        
        with pytest.raises(Exception):
            endpoint.path = "/new"


@pytest.mark.unit
class TestSchema:
    """Тесты для Schema"""
    
    def test_schema_creation(self):
        """Тест создания Schema"""
        definition = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"}
            }
        }
        schema = Schema(
            name="User",
            definition=definition
        )
        
        assert schema.name == "User"
        assert schema.definition == definition
    
    def test_immutability(self):
        """Тест неизменяемости Schema"""
        schema = Schema(
            name="User",
            definition={"type": "object"}
        )
        
        with pytest.raises(Exception):
            schema.name = "NewUser"


@pytest.mark.unit
class TestEndpointFilter:
    """Тесты для EndpointFilter"""
    
    def test_matches_exact(self):
        """Тест точного совпадения"""
        endpoints = {("GET", "/api/v1/users"), ("POST", "/api/v1/posts")}
        filter_obj = EndpointFilter.from_set(endpoints)
        
        assert filter_obj.matches("GET", "/api/v1/users") is True
        assert filter_obj.matches("POST", "/api/v1/posts") is True
        assert filter_obj.matches("GET", "/api/v1/posts") is False
    
    def test_matches_case_insensitive(self):
        """Тест совпадения с разным регистром метода"""
        endpoints = {("GET", "/api/v1/users")}
        filter_obj = EndpointFilter.from_set(endpoints)
        
        assert filter_obj.matches("get", "/api/v1/users") is True
        assert filter_obj.matches("Get", "/api/v1/users") is True
        assert filter_obj.matches("GET", "/api/v1/users") is True
    
    def test_matches_trailing_slash(self):
        """Тест совпадения с trailing slash"""
        endpoints = {("GET", "/api/v1/users/")}
        filter_obj = EndpointFilter.from_set(endpoints)
        
        assert filter_obj.matches("GET", "/api/v1/users") is True
        assert filter_obj.matches("GET", "/api/v1/users/") is True
    
    def test_matches_path_with_trailing_slash(self):
        """Тест совпадения когда путь в фильтре без trailing slash"""
        endpoints = {("GET", "/api/v1/users")}
        filter_obj = EndpointFilter.from_set(endpoints)
        
        assert filter_obj.matches("GET", "/api/v1/users/") is True
    
    def test_from_set_normalization(self):
        """Тест нормализации методов при создании из множества"""
        endpoints = {("get", "/test"), ("POST", "/test2")}
        filter_obj = EndpointFilter.from_set(endpoints)
        
        assert ("GET", "/test") in filter_obj.endpoints
        assert ("POST", "/test2") in filter_obj.endpoints
        assert ("get", "/test") not in filter_obj.endpoints
    
    def test_empty_filter(self):
        """Тест пустого фильтра"""
        filter_obj = EndpointFilter.empty()
        
        assert filter_obj.endpoints == set()
        assert filter_obj.matches("GET", "/any/path") is False
    
    def test_immutability(self):
        """Тест неизменяемости EndpointFilter"""
        endpoints = {("GET", "/test")}
        filter_obj = EndpointFilter.from_set(endpoints)
        
        with pytest.raises(Exception):
            filter_obj.endpoints = set()

