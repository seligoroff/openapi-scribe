"""Тесты для application/use_cases/verify_documentation.py"""
import pytest
from unittest.mock import Mock, mock_open, patch
from application.use_cases.verify_documentation import VerifyDocumentationUseCase
from domain.models import OpenAPISpec, Endpoint
from ports.spec_loader import SpecLoader


@pytest.mark.unit
class TestVerifyDocumentationUseCase:
    """Тесты для VerifyDocumentationUseCase"""
    
    def test_verify_endpoint_success(self, sample_openapi_spec, tmp_path):
        """Тест успешной проверки эндпоинта"""
        mock_loader = Mock(spec=SpecLoader)
        spec_obj = OpenAPISpec.from_dict(sample_openapi_spec)
        mock_loader.load.return_value = spec_obj
        
        # Создаем временный Markdown файл
        md_file = tmp_path / "test.md"
        md_file.write_text("""
### `GET` /api/v1/users
*Tag: users*

*ID операции:* `get_users`
*Краткое описание:* Get users

**Требования безопасности:**

- **CustomAPIKeyHeader**

##### Ответы
###### **Код 200:** Success
""", encoding='utf-8')
        
        use_case = VerifyDocumentationUseCase(mock_loader)
        
        result = use_case.verify_endpoint(
            spec_source="test.json",
            path="/api/v1/users",
            method="GET",
            markdown_file=str(md_file)
        )
        
        assert 'endpoint' in result
        assert 'has_issues' in result
        assert 'issues_count' in result
        assert 'issues' in result
        mock_loader.load.assert_called_once_with("test.json")
    
    def test_verify_endpoint_not_found(self, sample_openapi_spec):
        """Тест проверки несуществующего эндпоинта"""
        mock_loader = Mock(spec=SpecLoader)
        spec_obj = OpenAPISpec.from_dict(sample_openapi_spec)
        mock_loader.load.return_value = spec_obj
        
        use_case = VerifyDocumentationUseCase(mock_loader)
        
        with pytest.raises(ValueError, match="не найден"):
            use_case.verify_endpoint(
                spec_source="test.json",
                path="/api/v1/nonexistent",
                method="GET",
                markdown_file="/tmp/test.md"
            )
    
    def test_verify_endpoint_markdown_not_found(self, sample_openapi_spec):
        """Тест проверки с несуществующим Markdown файлом"""
        mock_loader = Mock(spec=SpecLoader)
        spec_obj = OpenAPISpec.from_dict(sample_openapi_spec)
        mock_loader.load.return_value = spec_obj
        
        use_case = VerifyDocumentationUseCase(mock_loader)
        
        with pytest.raises(FileNotFoundError):
            use_case.verify_endpoint(
                spec_source="test.json",
                path="/api/v1/users",
                method="GET",
                markdown_file="/nonexistent/file.md"
            )
    
    def test_verify_all_endpoints_success(self, sample_openapi_spec, tmp_path):
        """Тест проверки всех эндпоинтов"""
        mock_loader = Mock(spec=SpecLoader)
        spec_obj = OpenAPISpec.from_dict(sample_openapi_spec)
        mock_loader.load.return_value = spec_obj
        
        # Создаем временный Markdown файл
        md_file = tmp_path / "test.md"
        md_file.write_text("""
### `GET` /api/v1/users
*Tag: users*
""", encoding='utf-8')
        
        use_case = VerifyDocumentationUseCase(mock_loader)
        
        result = use_case.verify_all_endpoints(
            spec_source="test.json",
            markdown_file=str(md_file)
        )
        
        assert 'total_endpoints' in result
        assert 'endpoints_with_issues' in result
        assert 'total_issues' in result
        assert 'results' in result
        assert isinstance(result['results'], list)
        assert result['total_endpoints'] >= 0
    
    def test_verify_all_endpoints_with_filter(self, sample_openapi_spec, tmp_path):
        """Тест проверки всех эндпоинтов с фильтром"""
        mock_loader = Mock(spec=SpecLoader)
        spec_obj = OpenAPISpec.from_dict(sample_openapi_spec)
        mock_loader.load.return_value = spec_obj
        
        md_file = tmp_path / "test.md"
        md_file.write_text("""
### `GET` /api/v1/users
""", encoding='utf-8')
        
        use_case = VerifyDocumentationUseCase(mock_loader)
        
        result = use_case.verify_all_endpoints(
            spec_source="test.json",
            markdown_file=str(md_file),
            endpoints_filter=[("GET", "/api/v1/users")]
        )
        
        assert 'total_endpoints' in result
        assert result['total_endpoints'] <= 1  # Фильтр должен ограничить количество
    
    def test_verify_all_endpoints_markdown_not_found(self, sample_openapi_spec):
        """Тест проверки всех эндпоинтов с несуществующим Markdown файлом"""
        mock_loader = Mock(spec=SpecLoader)
        spec_obj = OpenAPISpec.from_dict(sample_openapi_spec)
        mock_loader.load.return_value = spec_obj
        
        use_case = VerifyDocumentationUseCase(mock_loader)
        
        with pytest.raises(FileNotFoundError):
            use_case.verify_all_endpoints(
                spec_source="test.json",
                markdown_file="/nonexistent/file.md"
            )

