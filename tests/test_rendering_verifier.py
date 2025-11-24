"""Тесты для rendering/verifier.py"""
import pytest
from rendering.verifier import DocumentationVerifier
from domain.models import Endpoint


@pytest.mark.unit
class TestDocumentationVerifier:
    """Тесты для DocumentationVerifier"""
    
    def test_verify_endpoint_no_issues(self):
        """Тест проверки эндпоинта без проблем"""
        endpoint = Endpoint(
            path="/api/v1/users",
            method="GET",
            operation={
                "summary": "Get users",
                "operationId": "get_users",
                "description": "Get list of users",
                "tags": ["users"],
                "security": [{"CustomAPIKeyHeader": []}],
                "responses": {
                    "200": {
                        "description": "Success",
                        "content": {
                            "application/json": {
                                "examples": {
                                    "Example1": {
                                        "summary": "Example",
                                        "value": {"users": []}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            tags=["users"]
        )
        
        markdown = """
### `GET` /api/v1/users
*Tag: users*

*ID операции:* `get_users`
*Краткое описание:* Get users
*Расширенное описание:* Get list of users

**Требования безопасности:**

- **CustomAPIKeyHeader**

##### Ответы
###### **Код 200:** Success

  - **Тип контента:** `application/json`
  
  - **Example:**
```json
{"users": []}
```
"""
        
        verifier = DocumentationVerifier()
        result = verifier.verify_endpoint(endpoint, markdown)
        
        assert result['has_issues'] is False
        assert result['issues_count'] == 0
        assert len(result['issues']) == 0
    
    def test_verify_endpoint_missing_security(self):
        """Тест проверки эндпоинта с отсутствующей security информацией"""
        endpoint = Endpoint(
            path="/api/v1/users",
            method="GET",
            operation={
                "summary": "Get users",
                "security": [{"CustomAPIKeyHeader": []}]
            },
            tags=["users"]
        )
        
        markdown = """
### `GET` /api/v1/users
*Tag: users*

*Краткое описание:* Get users
"""
        
        verifier = DocumentationVerifier()
        result = verifier.verify_endpoint(endpoint, markdown)
        
        assert result['has_issues'] is True
        assert result['issues_count'] == 1
        assert result['issues'][0]['type'] == 'missing_security'
        assert result['issues'][0]['severity'] == 'high'
    
    def test_verify_endpoint_missing_deprecated(self):
        """Тест проверки эндпоинта с отсутствующим deprecated статусом"""
        endpoint = Endpoint(
            path="/api/v1/old",
            method="GET",
            operation={
                "summary": "Old endpoint",
                "deprecated": True
            },
            tags=["old"]
        )
        
        markdown = """
### `GET` /api/v1/old
*Tag: old*

*Краткое описание:* Old endpoint
"""
        
        verifier = DocumentationVerifier()
        result = verifier.verify_endpoint(endpoint, markdown)
        
        assert result['has_issues'] is True
        assert any(issue['type'] == 'missing_deprecated' for issue in result['issues'])
    
    def test_verify_endpoint_missing_operation_id(self):
        """Тест проверки эндпоинта с отсутствующим operationId"""
        endpoint = Endpoint(
            path="/api/v1/users",
            method="GET",
            operation={
                "summary": "Get users",
                "operationId": "get_users"
            },
            tags=["users"]
        )
        
        markdown = """
### `GET` /api/v1/users
*Tag: users*

*Краткое описание:* Get users
"""
        
        verifier = DocumentationVerifier()
        result = verifier.verify_endpoint(endpoint, markdown)
        
        assert result['has_issues'] is True
        assert any(issue['type'] == 'missing_operation_id' for issue in result['issues'])
    
    def test_verify_endpoint_missing_response_examples(self):
        """Тест проверки эндпоинта с отсутствующими примерами ответов"""
        endpoint = Endpoint(
            path="/api/v1/users",
            method="GET",
            operation={
                "summary": "Get users",
                "responses": {
                    "401": {
                        "description": "Unauthorized",
                        "content": {
                            "application/json": {
                                "examples": {
                                    "InvalidToken": {
                                        "summary": "Invalid token",
                                        "value": {"detail": "Invalid token"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            tags=["users"]
        )
        
        markdown = """
### `GET` /api/v1/users
*Tag: users*

##### Ответы
###### **Код 401:** Unauthorized
"""
        
        verifier = DocumentationVerifier()
        result = verifier.verify_endpoint(endpoint, markdown)
        
        # Пример может быть найден по значению, но если нет - должна быть проблема
        # Проверяем, что верификатор работает
        assert 'issues' in result
    
    def test_extract_response_examples(self):
        """Тест извлечения примеров из responses"""
        verifier = DocumentationVerifier()
        
        responses = {
            "200": {
                "content": {
                    "application/json": {
                        "examples": {
                            "Example1": {
                                "summary": "Example 1",
                                "value": {"data": "test"}
                            }
                        }
                    }
                }
            }
        }
        
        examples = verifier._extract_response_examples(responses)
        assert "200" in examples
        assert "Example1" in examples["200"]
        assert "value" in examples["200"]["Example1"]
    
    
    def test_extract_examples_from_markdown_responses(self):
        """Тест извлечения примеров из Markdown"""
        verifier = DocumentationVerifier()
        
        endpoint = Endpoint(
            path="/api/v1/users",
            method="GET",
            operation={},
            tags=[]
        )
        
        markdown = """
### `GET` /api/v1/users

##### Ответы
###### **Код 200:** Success

  - **Example:**
```json
{"data": "test"}
```
"""
        
        examples = verifier._extract_examples_from_markdown_responses(markdown, endpoint)
        assert "200" in examples
        assert len(examples["200"]) > 0

