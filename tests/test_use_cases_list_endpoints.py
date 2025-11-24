"""Тесты для application/use_cases/list_endpoints.py"""
import pytest
from unittest.mock import Mock
from application.use_cases.list_endpoints import ListEndpointsUseCase
from domain.models import OpenAPISpec, Endpoint
from ports.spec_loader import SpecLoader


@pytest.mark.unit
class TestListEndpointsUseCase:
    """Тесты для ListEndpointsUseCase"""
    
    def test_execute_success(self, sample_openapi_spec):
        """Тест успешного выполнения use case"""
        mock_loader = Mock(spec=SpecLoader)
        spec_obj = OpenAPISpec.from_dict(sample_openapi_spec)
        mock_loader.load.return_value = spec_obj
        
        use_case = ListEndpointsUseCase(mock_loader)
        
        result = use_case.execute("test.json")
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(e, Endpoint) for e in result)
        mock_loader.load.assert_called_once_with("test.json")
    
    def test_execute_empty_spec(self, minimal_openapi_spec):
        """Тест выполнения с пустой спецификацией"""
        mock_loader = Mock(spec=SpecLoader)
        spec_obj = OpenAPISpec.from_dict(minimal_openapi_spec)
        mock_loader.load.return_value = spec_obj
        
        use_case = ListEndpointsUseCase(mock_loader)
        
        result = use_case.execute("test.json")
        
        assert isinstance(result, list)
        # Минимальная спецификация может не иметь эндпоинтов
    
    def test_execute_file_not_found(self):
        """Тест обработки случая, когда файл не найден"""
        mock_loader = Mock(spec=SpecLoader)
        mock_loader.load.side_effect = FileNotFoundError("Файл не найден")
        
        use_case = ListEndpointsUseCase(mock_loader)
        
        with pytest.raises(FileNotFoundError):
            use_case.execute("nonexistent.json")
    
    def test_execute_io_error(self):
        """Тест обработки IO ошибки"""
        mock_loader = Mock(spec=SpecLoader)
        mock_loader.load.side_effect = IOError("Ошибка чтения")
        
        use_case = ListEndpointsUseCase(mock_loader)
        
        with pytest.raises(IOError):
            use_case.execute("test.json")

