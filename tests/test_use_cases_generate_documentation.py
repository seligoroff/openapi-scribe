"""Тесты для application/use_cases/generate_documentation.py"""
import pytest
from unittest.mock import Mock, patch
from application.use_cases.generate_documentation import GenerateDocumentationUseCase
from domain.models import OpenAPISpec
from ports.spec_loader import SpecLoader


@pytest.mark.unit
class TestGenerateDocumentationUseCase:
    """Тесты для GenerateDocumentationUseCase"""
    
    def test_execute_success(self, sample_openapi_spec):
        """Тест успешного выполнения use case"""
        mock_loader = Mock(spec=SpecLoader)
        spec_obj = OpenAPISpec.from_dict(sample_openapi_spec)
        mock_loader.load.return_value = spec_obj
        
        with patch('application.use_cases.generate_documentation.MarkdownGenerator') as MockGenerator:
            mock_gen_instance = Mock()
            mock_gen_instance.generate.return_value = "# Test Documentation"
            MockGenerator.return_value = mock_gen_instance
            
            use_case = GenerateDocumentationUseCase(mock_loader)
            result = use_case.execute("test.json")
            
            assert result == "# Test Documentation"
            mock_loader.load.assert_called_once_with("test.json")
            mock_gen_instance.generate.assert_called_once()
    
    def test_execute_with_filter(self, sample_openapi_spec, endpoints_filter_file):
        """Тест выполнения с фильтром эндпоинтов"""
        mock_loader = Mock(spec=SpecLoader)
        spec_obj = OpenAPISpec.from_dict(sample_openapi_spec)
        mock_loader.load.return_value = spec_obj
        
        with patch('application.use_cases.generate_documentation.MarkdownGenerator') as MockGenerator:
            mock_gen_instance = Mock()
            mock_gen_instance.generate.return_value = "# Filtered Documentation"
            MockGenerator.return_value = mock_gen_instance
            
            use_case = GenerateDocumentationUseCase(mock_loader)
            result = use_case.execute("test.json", endpoints_filter=endpoints_filter_file)
            
            assert result == "# Filtered Documentation"
            mock_gen_instance.generate.assert_called_once()
            # Проверяем, что фильтр был передан
            call_args = mock_gen_instance.generate.call_args
            assert call_args[1]['endpoints_filter'] is not None
    
    def test_execute_with_all_schemas(self, sample_openapi_spec):
        """Тест выполнения с включением всех схем"""
        mock_loader = Mock(spec=SpecLoader)
        spec_obj = OpenAPISpec.from_dict(sample_openapi_spec)
        mock_loader.load.return_value = spec_obj
        
        with patch('application.use_cases.generate_documentation.MarkdownGenerator') as MockGenerator:
            mock_gen_instance = Mock()
            mock_gen_instance.generate.return_value = "# Documentation with all schemas"
            MockGenerator.return_value = mock_gen_instance
            
            use_case = GenerateDocumentationUseCase(mock_loader)
            result = use_case.execute("test.json", include_all_schemas=True)
            
            assert result == "# Documentation with all schemas"
            # Проверяем, что generate вызван с include_all_schemas=True
            call_args = mock_gen_instance.generate.call_args
            assert call_args[1]['include_all_schemas'] is True
    
    def test_execute_filter_file_not_found(self, sample_openapi_spec):
        """Тест обработки случая, когда файл фильтра не найден"""
        mock_loader = Mock(spec=SpecLoader)
        spec_obj = OpenAPISpec.from_dict(sample_openapi_spec)
        mock_loader.load.return_value = spec_obj
        
        with patch('application.use_cases.generate_documentation.MarkdownGenerator') as MockGenerator:
            mock_gen_instance = Mock()
            mock_gen_instance.generate.return_value = "# Documentation"
            MockGenerator.return_value = mock_gen_instance
            
            use_case = GenerateDocumentationUseCase(mock_loader)
            # Передаем несуществующий файл фильтра
            result = use_case.execute("test.json", endpoints_filter="/nonexistent/filter.txt")
            
            # Должен продолжить без фильтра
            assert result == "# Documentation"
            mock_gen_instance.generate.assert_called_once()
            # Проверяем, что фильтр None (файл не найден)
            call_args = mock_gen_instance.generate.call_args
            assert call_args[1]['endpoints_filter'] is None
    
    def test_execute_file_not_found(self):
        """Тест обработки случая, когда файл спецификации не найден"""
        mock_loader = Mock(spec=SpecLoader)
        mock_loader.load.side_effect = FileNotFoundError("Файл не найден")
        
        use_case = GenerateDocumentationUseCase(mock_loader)
        
        with pytest.raises(FileNotFoundError):
            use_case.execute("nonexistent.json")
    
    def test_execute_io_error(self):
        """Тест обработки IO ошибки"""
        mock_loader = Mock(spec=SpecLoader)
        mock_loader.load.side_effect = IOError("Ошибка чтения")
        
        use_case = GenerateDocumentationUseCase(mock_loader)
        
        with pytest.raises(IOError):
            use_case.execute("test.json")

