"""Тесты для application/use_cases/get_schema_info.py"""
import pytest
from unittest.mock import Mock
from application.use_cases.get_schema_info import GetSchemaInfoUseCase
from domain.models import OpenAPISpec, Schema
from ports.spec_loader import SpecLoader


@pytest.mark.unit
class TestGetSchemaInfoUseCase:
    """Тесты для GetSchemaInfoUseCase"""
    
    def test_execute_success(self, sample_openapi_spec):
        """Тест успешного выполнения use case"""
        mock_loader = Mock(spec=SpecLoader)
        spec_obj = OpenAPISpec.from_dict(sample_openapi_spec)
        mock_loader.load.return_value = spec_obj
        
        use_case = GetSchemaInfoUseCase(mock_loader)
        
        result = use_case.execute("test.json", "User")
        
        assert result is not None
        assert isinstance(result, Schema)
        assert result.name == "User"
        assert "type" in result.definition
        mock_loader.load.assert_called_once_with("test.json")
    
    def test_execute_schema_not_found(self, sample_openapi_spec):
        """Тест обработки случая, когда схема не найдена"""
        mock_loader = Mock(spec=SpecLoader)
        spec_obj = OpenAPISpec.from_dict(sample_openapi_spec)
        mock_loader.load.return_value = spec_obj
        
        use_case = GetSchemaInfoUseCase(mock_loader)
        
        result = use_case.execute("test.json", "NonexistentSchema")
        
        assert result is None
    
    def test_execute_file_not_found(self):
        """Тест обработки случая, когда файл не найден"""
        mock_loader = Mock(spec=SpecLoader)
        mock_loader.load.side_effect = FileNotFoundError("Файл не найден")
        
        use_case = GetSchemaInfoUseCase(mock_loader)
        
        with pytest.raises(FileNotFoundError):
            use_case.execute("nonexistent.json", "User")
    
    def test_execute_io_error(self):
        """Тест обработки IO ошибки"""
        mock_loader = Mock(spec=SpecLoader)
        mock_loader.load.side_effect = IOError("Ошибка чтения")
        
        use_case = GetSchemaInfoUseCase(mock_loader)
        
        with pytest.raises(IOError):
            use_case.execute("test.json", "User")

