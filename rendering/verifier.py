"""Верификатор для проверки информационных потерь в Markdown документации"""
import json
import re
from typing import Dict, List, Set, Optional
from domain.models import Endpoint


class DocumentationVerifier:
    """
    Верификатор для проверки полноты информации в сгенерированной Markdown документации.
    
    Сравнивает данные из OpenAPI спецификации с тем, что попало в Markdown,
    и находит информационные потери.
    """
    
    def verify_endpoint(
        self,
        endpoint: Endpoint,
        markdown_content: str
    ) -> Dict:
        """
        Проверяет полноту информации об эндпоинте в Markdown.
        
        Args:
            endpoint: Эндпоинт из OpenAPI спецификации
            markdown_content: Содержимое Markdown документации
            
        Returns:
            Словарь с результатами проверки и найденными потерями
        """
        operation = endpoint.operation
        issues = []
        missing_items = {
            'security': [],
            'response_examples': [],
            'parameter_examples': [],
            'request_body_examples': [],
            'deprecated': False,
            'operation_id': False,
            'description': False,
        }
        
        # Проверка security
        if 'security' in operation and operation['security']:
            security_info = self._extract_security_from_markdown(markdown_content, endpoint)
            if not security_info:
                # Проверяем еще раз более точно
                pattern = rf"###\s*`{endpoint.method}`\s+{re.escape(endpoint.path)}"
                match = re.search(pattern, markdown_content)
                if match:
                    endpoint_section = markdown_content[match.start():match.start() + 3000]
                    # Ищем "Требования безопасности" или "security"
                    if 'требования безопасности' in endpoint_section.lower() or 'security' in endpoint_section.lower():
                        security_info = True
                
                if not security_info:
                    missing_items['security'] = operation['security']
                    issues.append({
                        'type': 'missing_security',
                        'severity': 'high',
                        'message': f"Security информация отсутствует в Markdown: {json.dumps(operation['security'], ensure_ascii=False)}"
                    })
        
        # Проверка deprecated
        if operation.get('deprecated', False):
            if not self._check_deprecated_in_markdown(markdown_content, endpoint):
                missing_items['deprecated'] = True
                issues.append({
                    'type': 'missing_deprecated',
                    'severity': 'medium',
                    'message': "Deprecated статус не отображается в Markdown"
                })
        
        # Проверка operationId
        if 'operationId' in operation:
            if not self._check_operation_id_in_markdown(markdown_content, operation['operationId']):
                missing_items['operation_id'] = True
                issues.append({
                    'type': 'missing_operation_id',
                    'severity': 'low',
                    'message': f"OperationId не найден в Markdown: {operation['operationId']}"
                })
        
        # Проверка description
        if 'description' in operation and operation['description']:
            if not self._check_description_in_markdown(markdown_content, operation['description']):
                missing_items['description'] = True
                issues.append({
                    'type': 'missing_description',
                    'severity': 'medium',
                    'message': "Расширенное описание отсутствует в Markdown"
                })
        
        # Проверка примеров в responses
        response_examples = self._extract_response_examples(operation.get('responses', {}))
        markdown_response_examples = self._extract_examples_from_markdown_responses(markdown_content, endpoint)
        
        for code, examples in response_examples.items():
            markdown_examples = markdown_response_examples.get(code, [])
            # Получаем также значения примеров для сравнения
            markdown_example_values = self._extract_example_values_from_markdown(markdown_content, endpoint, code)
            
            for example_name, example_info in examples.items():
                # Получаем значение и summary
                if isinstance(example_info, dict) and 'value' in example_info:
                    example_value = example_info['value']
                    example_summary = example_info.get('summary', example_name)
                else:
                    example_value = example_info
                    example_summary = example_name
                
                # Проверяем по имени (ключ), summary и по значению
                found = False
                # Ищем по ключу (имени примера)
                if example_name in markdown_examples:
                    found = True
                # Ищем по summary (как отображается в Markdown)
                elif example_summary in markdown_examples:
                    found = True
                # Ищем по значению (сравниваем JSON)
                elif example_value in markdown_example_values:
                    found = True
                # Ищем по содержимому значения (для словарей)
                elif isinstance(example_value, dict):
                    example_json = json.dumps(example_value, sort_keys=True, ensure_ascii=False)
                    for md_value in markdown_example_values:
                        if isinstance(md_value, dict):
                            md_json = json.dumps(md_value, sort_keys=True, ensure_ascii=False)
                            if example_json == md_json:
                                found = True
                                break
                        elif isinstance(md_value, str) and example_json in md_value:
                            found = True
                            break
                
                if not found:
                    missing_items['response_examples'].append({
                        'code': code,
                        'name': example_name,
                        'value': example_value
                    })
                    issues.append({
                        'type': 'missing_response_example',
                        'severity': 'medium',
                        'message': f"Пример ответа {code} '{example_name}' отсутствует в Markdown"
                    })
        
        # Проверка примеров в parameters
        parameter_examples = self._extract_parameter_examples(operation.get('parameters', []))
        markdown_param_examples = self._extract_examples_from_markdown_parameters(markdown_content, endpoint)
        
        for param_name, examples in parameter_examples.items():
            markdown_examples = markdown_param_examples.get(param_name, [])
            for example in examples:
                if example not in markdown_examples:
                    missing_items['parameter_examples'].append({
                        'parameter': param_name,
                        'example': example
                    })
                    issues.append({
                        'type': 'missing_parameter_example',
                        'severity': 'low',
                        'message': f"Пример параметра '{param_name}' отсутствует в Markdown"
                    })
        
        # Проверка примеров в requestBody
        request_body_examples = self._extract_request_body_examples(operation.get('requestBody', {}))
        markdown_body_examples = self._extract_examples_from_markdown_request_body(markdown_content, endpoint)
        
        for example_name, example_value in request_body_examples.items():
            if example_name not in markdown_body_examples:
                missing_items['request_body_examples'].append({
                    'name': example_name,
                    'value': example_value
                })
                issues.append({
                    'type': 'missing_request_body_example',
                    'severity': 'medium',
                    'message': f"Пример тела запроса '{example_name}' отсутствует в Markdown"
                })
        
        return {
            'endpoint': f"{endpoint.method} {endpoint.path}",
            'has_issues': len(issues) > 0,
            'issues_count': len(issues),
            'issues': issues,
            'missing_items': missing_items,
            'summary': self._generate_summary(issues)
        }
    
    def _extract_security_from_markdown(self, markdown: str, endpoint: Endpoint) -> bool:
        """Проверяет наличие security информации в Markdown"""
        # Ищем секцию security в Markdown
        pattern = rf"###\s*`{endpoint.method}`\s+{re.escape(endpoint.path)}"
        match = re.search(pattern, markdown)
        if not match:
            return False
        
        # Ищем security после заголовка эндпоинта
        endpoint_section = markdown[match.start():match.start() + 2000]
        return 'security' in endpoint_section.lower() or 'авторизация' in endpoint_section.lower() or 'аутентификация' in endpoint_section.lower()
    
    def _check_deprecated_in_markdown(self, markdown: str, endpoint: Endpoint) -> bool:
        """Проверяет наличие deprecated статуса в Markdown"""
        pattern = rf"###\s*`{endpoint.method}`\s+{re.escape(endpoint.path)}"
        match = re.search(pattern, markdown)
        if not match:
            return False
        
        endpoint_section = markdown[match.start():match.start() + 500]
        return 'устарел' in endpoint_section.lower() or 'deprecated' in endpoint_section.lower() or '⚠️' in endpoint_section
    
    def _check_operation_id_in_markdown(self, markdown: str, operation_id: str) -> bool:
        """Проверяет наличие operationId в Markdown"""
        return operation_id in markdown
    
    def _check_description_in_markdown(self, markdown: str, description: str) -> bool:
        """Проверяет наличие description в Markdown"""
        # Берем первые 50 символов описания для поиска
        description_snippet = description[:50].strip()
        if not description_snippet:
            return True  # Пустое описание не считается потерей
        
        # Ищем описание в Markdown (может быть сокращено или отформатировано)
        return description_snippet.lower() in markdown.lower()
    
    def _extract_response_examples(self, responses: Dict) -> Dict[str, Dict]:
        """Извлекает примеры из responses"""
        examples = {}
        for code, response in responses.items():
            if not response:
                continue
            
            code_examples = {}
            for content_type, media in response.get('content', {}).items():
                if 'examples' in media:
                    for name, example_data in media['examples'].items():
                        if isinstance(example_data, dict) and 'value' in example_data:
                            # Сохраняем и имя (ключ), и summary для поиска
                            code_examples[name] = {
                                'value': example_data['value'],
                                'summary': example_data.get('summary', name)
                            }
                        else:
                            code_examples[name] = {'value': example_data, 'summary': name}
            
            if code_examples:
                examples[code] = code_examples
        
        return examples
    
    def _extract_examples_from_markdown_responses(self, markdown: str, endpoint: Endpoint) -> Dict[str, List[str]]:
        """Извлекает примеры из секции responses в Markdown"""
        examples = {}
        
        # Ищем секцию с ответами для этого эндпоинта
        pattern = rf"###\s*`{endpoint.method}`\s+{re.escape(endpoint.path)}"
        match = re.search(pattern, markdown)
        if not match:
            return examples
        
        endpoint_section = markdown[match.start():]
        
        # Ищем коды ответов
        response_pattern = r"######\s*\*\*Код\s+(\d+):\*\*"
        for match in re.finditer(response_pattern, endpoint_section):
            code = match.group(1)
            # Ищем примеры после кода ответа (ищем заголовки примеров)
            code_section = endpoint_section[match.start():match.start() + 2000]
            # Ищем паттерн **Название:** перед блоком кода
            example_names = re.findall(r'\*\*([^*]+):\*\*', code_section)
            examples[code] = example_names
        
        return examples
    
    def _extract_example_values_from_markdown(self, markdown: str, endpoint: Endpoint, code: str) -> List:
        """Извлекает значения примеров из Markdown для сравнения"""
        values = []
        
        # Ищем секцию с ответами для этого эндпоинта
        pattern = rf"###\s*`{endpoint.method}`\s+{re.escape(endpoint.path)}"
        match = re.search(pattern, markdown)
        if not match:
            return values
        
        endpoint_section = markdown[match.start():]
        
        # Ищем код ответа
        response_pattern = rf"######\s*\*\*Код\s+{code}:\*\*"
        match = re.search(response_pattern, endpoint_section)
        if not match:
            return values
        
        # Ищем блоки кода с примерами после кода ответа
        code_section = endpoint_section[match.start():match.start() + 3000]
        # Ищем блоки ```json ... ```
        json_blocks = re.findall(r'```json\s*\n(.*?)\n```', code_section, re.DOTALL)
        
        for json_block in json_blocks:
            try:
                parsed = json.loads(json_block.strip())
                values.append(parsed)
            except json.JSONDecodeError:
                # Если не JSON, добавляем как строку
                values.append(json_block.strip())
        
        return values
    
    def _extract_parameter_examples(self, parameters: List[Dict]) -> Dict[str, List]:
        """Извлекает примеры из parameters"""
        examples = {}
        for param in parameters:
            param_name = param.get('name', '')
            param_examples = []
            
            # Примеры из schema
            if 'schema' in param and param['schema']:
                schema = param['schema']
                if 'examples' in schema:
                    if isinstance(schema['examples'], list):
                        param_examples.extend(schema['examples'])
                    elif isinstance(schema['examples'], dict):
                        param_examples.extend(schema['examples'].values())
                if 'example' in schema:
                    param_examples.append(schema['example'])
            
            # Примеры из самого параметра
            if 'examples' in param:
                if isinstance(param['examples'], list):
                    param_examples.extend(param['examples'])
                elif isinstance(param['examples'], dict):
                    param_examples.extend(param['examples'].values())
            if 'example' in param:
                param_examples.append(param['example'])
            
            if param_examples:
                examples[param_name] = param_examples
        
        return examples
    
    def _extract_examples_from_markdown_parameters(self, markdown: str, endpoint: Endpoint) -> Dict[str, List]:
        """Извлекает примеры из секции parameters в Markdown"""
        examples = {}
        
        pattern = rf"###\s*`{endpoint.method}`\s+{re.escape(endpoint.path)}"
        match = re.search(pattern, markdown)
        if not match:
            return examples
        
        endpoint_section = markdown[match.start():match.start() + 3000]
        
        # Ищем секцию с примерами параметров
        param_examples_pattern = r"#### Примеры параметров\s*\*\*([^*]+)\*\*\s*\*\*Пример\s+\d+:\*\*\s*`([^`]+)`"
        for match in re.finditer(param_examples_pattern, endpoint_section):
            param_name = match.group(1)
            example_value = match.group(2)
            if param_name not in examples:
                examples[param_name] = []
            examples[param_name].append(example_value)
        
        return examples
    
    def _extract_request_body_examples(self, request_body: Dict) -> Dict[str, any]:
        """Извлекает примеры из requestBody"""
        examples = {}
        
        for content_type, media in request_body.get('content', {}).items():
            if 'examples' in media:
                for name, example_data in media['examples'].items():
                    if isinstance(example_data, dict) and 'value' in example_data:
                        examples[name] = example_data['value']
                    else:
                        examples[name] = example_data
            if 'example' in media:
                examples['default'] = media['example']
        
        return examples
    
    def _extract_examples_from_markdown_request_body(self, markdown: str, endpoint: Endpoint) -> List[str]:
        """Извлекает примеры из секции requestBody в Markdown"""
        examples = []
        
        pattern = rf"###\s*`{endpoint.method}`\s+{re.escape(endpoint.path)}"
        match = re.search(pattern, markdown)
        if not match:
            return examples
        
        endpoint_section = markdown[match.start():match.start() + 5000]
        
        # Ищем примеры в секции requestBody
        example_pattern = r'\*\*([^*]+):\*\*'
        found_examples = re.findall(example_pattern, endpoint_section)
        examples.extend(found_examples)
        
        return examples
    
    def _generate_summary(self, issues: List[Dict]) -> str:
        """Генерирует краткое резюме найденных проблем"""
        if not issues:
            return "✅ Информационных потерь не обнаружено"
        
        high_count = sum(1 for i in issues if i['severity'] == 'high')
        medium_count = sum(1 for i in issues if i['severity'] == 'medium')
        low_count = sum(1 for i in issues if i['severity'] == 'low')
        
        summary_parts = []
        if high_count > 0:
            summary_parts.append(f"🔴 Критичных: {high_count}")
        if medium_count > 0:
            summary_parts.append(f"🟡 Средних: {medium_count}")
        if low_count > 0:
            summary_parts.append(f"🟢 Низких: {low_count}")
        
        return f"Найдено проблем: {len(issues)} ({', '.join(summary_parts)})"

