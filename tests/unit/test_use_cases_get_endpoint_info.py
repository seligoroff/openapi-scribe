"""Тесты для application/use_cases/get_endpoint_info.py"""
import pytest
from unittest.mock import Mock
from application.use_cases.get_endpoint_info import GetEndpointInfoUseCase
from domain.models import OpenAPISpec, Endpoint
from ports.spec_loader import SpecLoader


@pytest.mark.unit
class TestGetEndpointInfoUseCase:
    """Тесты для GetEndpointInfoUseCase"""
    
    def test_execute_success(self, sample_openapi_spec):
        """Тест успешного выполнения use case"""
        # Создаем мок SpecLoader
        mock_loader = Mock(spec=SpecLoader)
        spec_obj = OpenAPISpec.from_dict(sample_openapi_spec)
        mock_loader.load.return_value = spec_obj
        
        # Создаем use case
        use_case = GetEndpointInfoUseCase(mock_loader)
        
        # Выполняем
        result = use_case.execute("test.json", "/api/v1/users", "GET")
        
        # Проверяем результат
        assert result is not None
        assert isinstance(result, Endpoint)
        assert result.path == "/api/v1/users"
        assert result.method == "GET"
        mock_loader.load.assert_called_once_with("test.json")
    
    def test_execute_endpoint_not_found(self, sample_openapi_spec):
        """Тест обработки случая, когда эндпоинт не найден"""
        mock_loader = Mock(spec=SpecLoader)
        spec_obj = OpenAPISpec.from_dict(sample_openapi_spec)
        mock_loader.load.return_value = spec_obj
        
        use_case = GetEndpointInfoUseCase(mock_loader)
        
        with pytest.raises(ValueError, match="не найден"):
            use_case.execute("test.json", "/nonexistent", "GET")
    
    def test_execute_method_not_found(self, sample_openapi_spec):
        """Тест обработки случая, когда метод не найден"""
        mock_loader = Mock(spec=SpecLoader)
        spec_obj = OpenAPISpec.from_dict(sample_openapi_spec)
        mock_loader.load.return_value = spec_obj
        
        use_case = GetEndpointInfoUseCase(mock_loader)
        
        with pytest.raises(ValueError, match="Метод"):
            use_case.execute("test.json", "/api/v1/users", "DELETE")
    
    def test_execute_file_not_found(self):
        """Тест обработки случая, когда файл не найден"""
        mock_loader = Mock(spec=SpecLoader)
        mock_loader.load.side_effect = FileNotFoundError("Файл не найден")
        
        use_case = GetEndpointInfoUseCase(mock_loader)
        
        with pytest.raises(FileNotFoundError):
            use_case.execute("nonexistent.json", "/api/v1/users", "GET")
    
    def test_execute_io_error(self):
        """Тест обработки IO ошибки"""
        mock_loader = Mock(spec=SpecLoader)
        mock_loader.load.side_effect = IOError("Ошибка чтения")
        
        use_case = GetEndpointInfoUseCase(mock_loader)
        
        with pytest.raises(IOError):
            use_case.execute("test.json", "/api/v1/users", "GET")

