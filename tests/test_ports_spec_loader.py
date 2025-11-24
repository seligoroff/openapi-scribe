"""Тесты для ports/spec_loader.py"""
import pytest
from unittest.mock import Mock, patch
from ports.spec_loader import SpecLoader
from domain.models import OpenAPISpec


class MockSpecLoader(SpecLoader):
    """Мок-реализация SpecLoader для тестирования"""
    
    def __init__(self, return_value=None, raise_exception=None):
        """
        Args:
            return_value: Значение для возврата из load()
            raise_exception: Исключение для выброса из load()
        """
        self.return_value = return_value
        self.raise_exception = raise_exception
        self.load_called_with = None
    
    def load(self, source: str) -> OpenAPISpec:
        """Мок-реализация load()"""
        self.load_called_with = source
        
        if self.raise_exception:
            raise self.raise_exception
        
        if self.return_value:
            return self.return_value
        
        # Возвращаем минимальную спецификацию по умолчанию
        spec_dict = {
            "openapi": "3.0.0",
            "info": {"title": "Mock API", "version": "1.0.0"},
            "paths": {},
            "components": {"schemas": {}}
        }
        return OpenAPISpec.from_dict(spec_dict)


@pytest.mark.unit
class TestSpecLoader:
    """Тесты для абстрактного порта SpecLoader"""
    
    def test_spec_loader_is_abstract(self):
        """Тест что SpecLoader является абстрактным классом"""
        # Нельзя создать экземпляр абстрактного класса
        with pytest.raises(TypeError):
            SpecLoader()
    
    def test_spec_loader_has_load_method(self):
        """Тест что SpecLoader имеет метод load"""
        assert hasattr(SpecLoader, 'load')
        assert callable(getattr(SpecLoader, 'load'))
    
    def test_mock_loader_implements_interface(self):
        """Тест что MockSpecLoader реализует интерфейс"""
        loader = MockSpecLoader()
        assert isinstance(loader, SpecLoader)
    
    def test_load_method_signature(self):
        """Тест сигнатуры метода load"""
        loader = MockSpecLoader()
        spec = loader.load("test_source")
        
        assert isinstance(spec, OpenAPISpec)
        assert loader.load_called_with == "test_source"
    
    def test_load_returns_openapi_spec(self):
        """Тест что load возвращает OpenAPISpec"""
        spec_dict = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {},
            "components": {"schemas": {}}
        }
        expected_spec = OpenAPISpec.from_dict(spec_dict)
        loader = MockSpecLoader(return_value=expected_spec)
        
        result = loader.load("test_source")
        
        assert isinstance(result, OpenAPISpec)
        assert result == expected_spec
    
    def test_load_raises_file_not_found(self):
        """Тест что load может выбросить FileNotFoundError"""
        loader = MockSpecLoader(raise_exception=FileNotFoundError("File not found"))
        
        with pytest.raises(FileNotFoundError):
            loader.load("nonexistent")
    
    def test_load_raises_value_error(self):
        """Тест что load может выбросить ValueError"""
        loader = MockSpecLoader(raise_exception=ValueError("Invalid spec"))
        
        with pytest.raises(ValueError):
            loader.load("invalid_source")
    
    def test_load_raises_io_error(self):
        """Тест что load может выбросить IOError"""
        loader = MockSpecLoader(raise_exception=IOError("Read error"))
        
        with pytest.raises(IOError):
            loader.load("source")
    
    def test_load_called_with_source(self):
        """Тест что load вызывается с правильным source"""
        loader = MockSpecLoader()
        loader.load("test/path.json")
        
        assert loader.load_called_with == "test/path.json"
    
    def test_load_with_different_sources(self):
        """Тест что load работает с разными источниками"""
        loader = MockSpecLoader()
        
        sources = [
            "file.json",
            "/absolute/path.json",
            "~/home/file.json",
            "http://example.com/spec.json"
        ]
        
        for source in sources:
            loader.load(source)
            assert loader.load_called_with == source
    
    def test_spec_loader_docstring(self):
        """Тест что SpecLoader имеет документацию"""
        assert SpecLoader.__doc__ is not None
        assert len(SpecLoader.__doc__.strip()) > 0
    
    def test_load_method_docstring(self):
        """Тест что метод load имеет документацию"""
        assert SpecLoader.load.__doc__ is not None
        assert len(SpecLoader.load.__doc__.strip()) > 0

