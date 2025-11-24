"""Генератор Markdown документации"""
import os
import json
from collections import defaultdict
from typing import Dict, Set, Optional, List
from jinja2 import Environment, FileSystemLoader

from domain.models import OpenAPISpec, Endpoint, EndpointFilter
from domain.services import SchemaResolver, SchemaCollector
from rendering.formatters import TypeFormatter, ExampleFormatter, DescriptionFormatter


class MarkdownGenerator:
    """
    Генератор Markdown документации из OpenAPI спецификации.
    
    Использует domain сервисы и форматтеры для генерации документации.
    """
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Инициализирует генератор.
        
        Args:
            template_dir: Путь к директории с шаблонами (по умолчанию rendering/templates)
        """
        if template_dir is None:
            # Используем шаблоны из rendering/templates
            template_dir = os.path.join(
                os.path.dirname(__file__),
                'templates'
            )
        
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Регистрация кастомных фильтров
        self.env.filters['format_example'] = lambda ex, max_length=100: ExampleFormatter.format(ex, max_length)
        self.env.filters['safe_replace'] = lambda s: DescriptionFormatter.safe_replace(s) if s else ""
    
    def generate(
        self,
        spec: OpenAPISpec,
        endpoints_filter: Optional[EndpointFilter] = None,
        include_all_schemas: bool = False
    ) -> str:
        """
        Генерирует Markdown документацию из OpenAPI спецификации.
        
        Args:
            spec: OpenAPI спецификация
            endpoints_filter: Фильтр эндпоинтов (опционально)
            include_all_schemas: Включить все схемы, а не только используемые
            
        Returns:
            Сгенерированная Markdown документация
        """
        # Инициализация domain сервисов
        resolver = SchemaResolver(spec)
        collector = SchemaCollector(spec, resolver)
        
        # Подготовка данных для основного шаблона
        context = {
            'title': spec.info.get('title', ''),
            'version': spec.info.get('version', ''),
            'description': spec.info.get('description', ''),
            'endpoints_by_tag': defaultdict(list),
            'schemas_section': '',
            'spec': spec.raw  # Передаем raw для обратной совместимости с шаблонами
        }
        
        # Собираем все используемые схемы
        used_schemas: Optional[Set[str]] = set() if not include_all_schemas else None
        
        # Группировка эндпоинтов по тегам
        for path, methods in spec.paths.items():
            for method, operation in methods.items():
                if method.lower() not in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']:
                    continue
                
                # Проверка фильтра эндпоинтов
                include_endpoint = True
                if endpoints_filter:
                    include_endpoint = endpoints_filter.matches(method, path)
                
                if include_endpoint:
                    tags = operation.get('tags', ['Без тега'])
                    endpoint = Endpoint(
                        path=path,
                        method=method,
                        operation=operation,
                        tags=tags
                    )
                    
                    for tag in tags:
                        endpoint_data = {
                            'path': path,
                            'method': method.upper(),
                            'details': operation,
                            'parameters_table': self._generate_parameters_table(operation.get('parameters', []), spec, resolver),
                            'request_body': self._generate_request_body(operation.get('requestBody', {}), spec, resolver) if 'requestBody' in operation else "",
                            'responses': self._generate_responses(operation.get('responses', {}), spec, resolver) if 'responses' in operation else "",
                            'security': self._generate_security(operation.get('security', [])) if 'security' in operation else ""
                        }
                        context['endpoints_by_tag'][tag].append(endpoint_data)
                    
                    # Сбор схем
                    if not include_all_schemas and used_schemas is not None:
                        collected = collector.collect_from_endpoint(endpoint)
                        used_schemas.update(collected)
        
        # Генерация секции схем
        context['schemas_section'] = self._generate_schemas(spec, resolver, used_schemas)
        
        # Рендеринг основного шаблона
        template = self.env.get_template('base.md.j2')
        return template.render(context)
    
    def _generate_parameters_table(
        self,
        parameters: List[Dict],
        spec: OpenAPISpec,
        resolver: SchemaResolver
    ) -> str:
        """Генерирует таблицу параметров через шаблон"""
        if not parameters:
            return ""
        
        # Подготовка данных для шаблона
        params_data = []
        for param in parameters:
            # Обработка ссылок через SchemaResolver
            resolved_param = param.copy()
            if 'schema' in param and param['schema']:
                resolved_schema = resolver.process_schema(param['schema'])
                resolved_param['schema'] = resolved_schema
            
            # Получение описания
            description = DescriptionFormatter.format(resolved_param)
            
            params_data.append({
                'name': resolved_param.get('name', ''),
                'type': TypeFormatter.format(resolved_param.get('schema', {})) if 'schema' in resolved_param else '',
                'in': resolved_param.get('in', ''),
                'required': "✅" if resolved_param.get('required', False) else "❌",
                'description': description,
                'examples': ExampleFormatter.extract(resolved_param),
                'format': resolved_param.get('schema', {}).get('format', '') if 'schema' in resolved_param else ''
            })
        
        template = self.env.get_template('parameters_table.md.j2')
        return template.render(parameters=params_data, spec=spec.raw)
    
    def _generate_request_body(
        self,
        body: Dict,
        spec: OpenAPISpec,
        resolver: SchemaResolver
    ) -> str:
        """Генерирует описание тела запроса через шаблон"""
        if not body:
            return ""
        
        body_data = {
            'description': body.get('description', ''),
            'content': []
        }
        
        for content_type, media in body.get('content', {}).items():
            content = {'content_type': content_type}
            
            if 'schema' in media and media['schema']:
                original_schema = media['schema']
                schema = resolver.process_schema(original_schema)
                
                if '$ref' in original_schema:
                    ref_name = original_schema['$ref'].split('/')[-1]
                    try:
                        ref_schema = resolver.resolve(original_schema['$ref'])
                        if ref_schema:
                            content['schema_title'] = ref_schema.get('title', '')
                    except Exception:
                        content['schema_title'] = ''
                    content['schema_ref'] = ref_name
                else:
                    content['schema_type'] = TypeFormatter.format(schema) if schema else ''
                
                # Обработка свойств объектов
                if schema and schema.get('type') == 'object' and 'properties' in schema:
                    content['properties'] = []
                    required_fields = schema.get('required', [])
                    
                    for prop_name, prop in schema['properties'].items():
                        if prop is None:
                            continue
                        
                        prop = resolver.process_schema(prop)
                        content['properties'].append({
                            'name': prop_name,
                            'type': TypeFormatter.format(prop) if prop else '',
                            'required': '✅' if prop_name in required_fields else '❌',
                            'description': DescriptionFormatter.format(prop),
                            'examples': ExampleFormatter.extract(prop),
                            'format': prop.get('format', '') if prop else ''
                        })
            
            content['examples'] = ExampleFormatter.extract(media)
            body_data['content'].append(content)
        
        template = self.env.get_template('request_body.md.j2')
        return template.render(body=body_data, spec=spec.raw)
    
    def _generate_responses(
        self,
        responses: Dict,
        spec: OpenAPISpec,
        resolver: SchemaResolver
    ) -> str:
        """Генерирует описание ответов через шаблон"""
        if not responses:
            return ""
        
        responses_data = []
        for code, response in responses.items():
            if response is None:
                continue
                
            response_data = {
                'code': code,
                'description': response.get('description', ''),
                'content': []
            }
            
            for content_type, media in response.get('content', {}).items():
                if media is None:
                    continue
                    
                content = {'content_type': content_type}
                
                if 'schema' in media and media['schema']:
                    schema = media['schema']
                    if '$ref' in schema:
                        ref_name = schema['$ref'].split('/')[-1]
                        try:
                            schema_ref = resolver.resolve(schema['$ref'])
                            if schema_ref:
                                content['schema_title'] = schema_ref.get('title', '')
                        except Exception:
                            content['schema_title'] = ''
                        content['schema_ref'] = ref_name
                    else:
                        processed_schema = resolver.process_schema(schema)
                        content['schema_type'] = TypeFormatter.format(processed_schema)
                
                content['examples'] = ExampleFormatter.extract(media)
                response_data['content'].append(content)
            
            responses_data.append(response_data)
        
        template = self.env.get_template('responses.md.j2')
        return template.render(responses=responses_data, spec=spec.raw)
    
    def _generate_security(self, security: List[Dict]) -> str:
        """Генерирует описание требований безопасности"""
        if not security:
            return ""
        
        security_items = []
        for sec in security:
            for scheme_name, scopes in sec.items():
                if scopes:
                    security_items.append(f"**{scheme_name}** (scopes: {', '.join(scopes)})")
                else:
                    security_items.append(f"**{scheme_name}**")
        
        if security_items:
            return f"\n**Требования безопасности:**\n\n" + "\n".join(f"- {item}" for item in security_items) + "\n"
        return ""
    
    def _generate_schemas(
        self,
        spec: OpenAPISpec,
        resolver: SchemaResolver,
        used_schemas: Optional[Set[str]] = None
    ) -> str:
        """Генерирует раздел со схемами данных через шаблон"""
        schemas = spec.schemas
        if not schemas:
            return ""
        
        if used_schemas is not None:
            schemas = {name: schema for name, schema in schemas.items() if name in used_schemas}
        
        if not schemas:
            return ""
        
        schemas_data = []
        for name, schema in schemas.items():
            if schema is None:
                continue
            
            # Обработка схемы через resolver
            processed_schema = resolver.process_schema(schema)
            
            schema_data = {
                'name': name,
                'title': processed_schema.get('title', ''),
                'type': processed_schema.get('type', 'object'),
                'description': processed_schema.get('description', ''),
                'required_fields': processed_schema.get('required', []),
                'properties': [],
                'example': processed_schema.get('example', None)
            }
            
            if 'properties' in processed_schema:
                required_fields = processed_schema.get('required', [])
                
                for prop_name, prop in processed_schema['properties'].items():
                    if prop is None:
                        continue
                    
                    prop = resolver.process_schema(prop)
                    schema_data['properties'].append({
                        'name': prop_name,
                        'type': TypeFormatter.format(prop) if prop else '',
                        'required': '✅' if prop_name in required_fields else '❌',
                        'description': DescriptionFormatter.format(prop),
                        'examples': ExampleFormatter.extract(prop),
                        'format': prop.get('format', '') if prop else ''
                    })
            
            schemas_data.append(schema_data)
        
        template = self.env.get_template('schemas.md.j2')
        return template.render(schemas=schemas_data, spec=spec.raw)

