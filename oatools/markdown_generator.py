import json
from collections import defaultdict
from .utils import process_schema, resolve_ref
from jinja2 import Environment, FileSystemLoader
import os

# Инициализация Jinja2
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True
)

# Регистрация кастомных фильтров
env.filters['format_example'] = lambda ex, max_length=100: format_example(ex, max_length)
env.filters['safe_replace'] = lambda s: safe_replace(s) if s else ""

def safe_replace(s):
    """Безопасная замена символов с защитой от None"""
    if s is None:
        return ""
    return s.replace('\n', '<br>').replace('  - ', '<br>- ')

def format_type(schema):
    """Улучшенное форматирование типов с полной обработкой вложенных ссылок"""
    # Проверка сохранённых оригинальных ссылок
    if 'x-original-ref' in schema:
        ref = schema['x-original-ref']
        if ref.startswith('#/components/schemas/'):
            ref_name = ref.split('/')[-1]
            return f"[{ref_name}](#{ref_name.lower()})"
    
    # Обработка обычных ссылок
    if '$ref' in schema:
        ref_name = schema['$ref'].split('/')[-1]
        return f"[{ref_name}](#{ref_name.lower()})"
    
    # Обработка additionalProperties
    if 'additionalProperties' in schema:
        if isinstance(schema['additionalProperties'], dict):
            value_type = format_type(schema['additionalProperties'])
            return f"object<string, {value_type}>"
        return "object"
    
    # Обработка комбинаторов схем
    if 'anyOf' in schema:
        types = [format_type(s) for s in schema['anyOf']]
        return f"anyOf<{' , '.join(types)}>"
    elif 'oneOf' in schema:
        types = [format_type(s) for s in schema['oneOf']]
        return f"oneOf<{' , '.join(types)}>"
    elif 'allOf' in schema:
        types = [format_type(s) for s in schema['allOf']]
        return f"allOf<{' & '.join(types)}>"
    
    # Улучшенная обработка массивов
    elif schema.get('type') == 'array' and 'items' in schema:
        items_schema = schema['items']
        
        # Рекурсивный вызов для вложенных элементов
        items_type = format_type(items_schema)
        
        # Определение типа элементов
        if 'type' in items_schema:
            base_type = items_schema['type']
        elif 'x-original-ref' in items_schema:
            ref_name = items_schema['x-original-ref'].split('/')[-1]
            base_type = f"[{ref_name}](#{ref_name.lower()})"
        elif '$ref' in items_schema:
            ref_name = items_schema['$ref'].split('/')[-1]
            base_type = f"[{ref_name}](#{ref_name.lower()})"
        else:
            base_type = 'object'
        
        # Форматирование для примитивных типов
        if base_type in ['string', 'integer', 'number', 'boolean']:
            return f"array<{base_type}>"
        
        # Форматирование для сложных типов
        return f"array<{items_type}>"
    
    # Обработка объектов с properties
    elif schema.get('type') == 'object' and 'properties' in schema:
        return "object"
    
    # Базовый тип
    return schema.get('type', 'object')

def get_description(node):
    """Извлекает описание с fallback на title"""
    return node.get('description') or node.get('title', '') or ""

def get_examples(node):
    """Извлекает все примеры из узла"""
    examples = []
    
    # Одиночный пример
    if 'example' in node:
        examples.append(('Пример', node['example']))
    
    # Множественные примеры
    if 'examples' in node:
        if isinstance(node['examples'], dict):
            for name, example_data in node['examples'].items():
                if isinstance(example_data, dict) and 'value' in example_data:
                    summary = example_data.get('summary', name)
                    examples.append((summary, example_data['value']))
                elif isinstance(example_data, dict) and 'value' not in example_data:
                    # Обработка случая, когда пример представлен напрямую
                    examples.append((name, example_data))
                else:
                    # Простое значение
                    examples.append((name, example_data))
        elif isinstance(node['examples'], list) and node['examples']:
            for i, example in enumerate(node['examples']):
                examples.append((f"Пример {i+1}", example))
    
    # Примеры из схемы (для параметров с schema)
    if 'schema' in node and isinstance(node['schema'], dict):
        schema = node['schema']
        if 'example' in schema:
            examples.append(('Пример', schema['example']))
        if 'examples' in schema:
            if isinstance(schema['examples'], dict):
                for name, example_data in schema['examples'].items():
                    if isinstance(example_data, dict) and 'value' in example_data:
                        summary = example_data.get('summary', name)
                        examples.append((summary, example_data['value']))
                    else:
                        examples.append((name, example_data))
            elif isinstance(schema['examples'], list):
                for i, example in enumerate(schema['examples']):
                    examples.append((f"Пример {i+1}", example))
        
    return examples

def format_example(example, max_length=150):
    """Форматирует пример для вывода"""
    if example is None:
        return ""
        
    if isinstance(example, (dict, list)):
        try:
            example_str = json.dumps(example, ensure_ascii=False, indent=2)
            if len(example_str) > max_length:
                return example_str[:max_length] + "..."
            return example_str
        except TypeError:
            return str(example)
    return str(example)

def collect_used_schemas(spec, node, collected):
    """Рекурсивно собирает все использованные схемы из узла спецификации"""
    if isinstance(node, dict):
        # Обработка ссылок
        if '$ref' in node:
            ref = node['$ref']
            if ref.startswith('#/components/schemas/'):
                schema_name = ref.split('/')[-1]
                if schema_name not in collected:
                    collected.add(schema_name)
                    # Рекурсивно обрабатываем саму схему
                    try:
                        schema_node = resolve_ref(spec, ref)
                        collect_used_schemas(spec, schema_node, collected)
                    except Exception:
                        pass  # Игнорируем ошибки разрешения ссылок
        
        # Обработка комбинаторов схем
        for key in ['allOf', 'anyOf', 'oneOf']:
            if key in node:
                for item in node[key]:
                    collect_used_schemas(spec, item, collected)
        
        # Обработка свойств объектов
        if 'properties' in node:
            for prop in node['properties'].values():
                collect_used_schemas(spec, prop, collected)
        
        # Обработка элементов массивов
        if 'items' in node:
            collect_used_schemas(spec, node['items'], collected)
        
        # Обработка additionalProperties
        if 'additionalProperties' in node and isinstance(node['additionalProperties'], dict):
            collect_used_schemas(spec, node['additionalProperties'], collected)
        
        # Рекурсивный обход
        for key, value in node.items():
            # Пропускаем уже обработанные ключи
            if key in ['$ref', 'allOf', 'anyOf', 'oneOf', 'properties', 'items', 'additionalProperties']:
                continue
            collect_used_schemas(spec, value, collected)
    
    elif isinstance(node, list):
        for item in node:
            collect_used_schemas(spec, item, collected)

def generate_parameters_table(parameters, spec):
    """Генерирует таблицу параметров через шаблон"""
    if not parameters:
        return ""
    
    # Подготовка данных для шаблона
    params_data = []
    for param in parameters:
        # Обработка ссылок
        resolved_param = param.copy()
        if 'schema' in param and param['schema']:
            resolved_param['schema'] = process_schema(spec, param['schema'])
        
        # Получение описания с защитой от None
        description = get_description(resolved_param)
        
        params_data.append({
            'name': resolved_param.get('name', ''),
            'type': format_type(resolved_param.get('schema', {})) if 'schema' in resolved_param else '',
            'in': resolved_param.get('in', ''),
            'required': "✅" if resolved_param.get('required', False) else "❌",
            'description': description,
            'examples': get_examples(resolved_param),
            'format': resolved_param.get('schema', {}).get('format', '') if 'schema' in resolved_param else ''
        })
    
    template = env.get_template('parameters_table.md.j2')
    # Передаем spec в шаблон
    return template.render(parameters=params_data, spec=spec)

def generate_request_body(body, spec):
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
            schema = process_schema(spec, original_schema) if original_schema else {}
            
            if '$ref' in original_schema:
                ref_name = original_schema['$ref'].split('/')[-1]
                try:
                    ref_schema = resolve_ref(spec, original_schema['$ref'])
                    content['schema_title'] = ref_schema.get('title', '')
                except Exception:
                    content['schema_title'] = ''
                content['schema_ref'] = ref_name
            else:
                content['schema_type'] = format_type(schema) if schema else ''
            
            # Обработка свойств объектов
            if schema and schema.get('type') == 'object' and 'properties' in schema:
                content['properties'] = []
                required_fields = schema.get('required', [])
                
                for prop_name, prop in schema['properties'].items():
                    if prop is None:
                        continue
                        
                    prop = process_schema(spec, prop)
                    content['properties'].append({
                        'name': prop_name,
                        'type': format_type(prop) if prop else '',
                        'required': '✅' if prop_name in required_fields else '❌',
                        'description': get_description(prop),
                        'examples': get_examples(prop),
                        'format': prop.get('format', '') if prop else ''
                    })
        
        content['examples'] = get_examples(media)
        body_data['content'].append(content)
    
    template = env.get_template('request_body.md.j2')
    # Передаем spec в шаблон
    return template.render(body=body_data, spec=spec)

def generate_responses(responses, spec):
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
                        schema_ref = resolve_ref(spec, schema['$ref'])
                        content['schema_title'] = schema_ref.get('title', '')
                    except Exception:
                        content['schema_title'] = ''
                    content['schema_ref'] = ref_name
                else:
                    content['schema_type'] = format_type(schema)
            
            content['examples'] = get_examples(media)
            response_data['content'].append(content)
        
        responses_data.append(response_data)
    
    template = env.get_template('responses.md.j2')
    # Передаем spec в шаблон
    return template.render(responses=responses_data, spec=spec)

def generate_schemas(spec, used_schemas=None):
    """Генерирует раздел со схемами данных через шаблон"""
    schemas = spec.get('components', {}).get('schemas', {})
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
            
        schema_data = {
            'name': name,
            'title': schema.get('title', ''),
            'type': schema.get('type', 'object'),
            'description': schema.get('description', ''),
            'required_fields': schema.get('required', []),
            'properties': [],
            'example': schema.get('example', None)
        }
        
        if 'properties' in schema:
            required_fields = schema.get('required', [])
            
            for prop_name, prop in schema['properties'].items():
                if prop is None:
                    continue
                    
                prop = process_schema(spec, prop)
                schema_data['properties'].append({
                    'name': prop_name,
                    'type': format_type(prop) if prop else '',
                    'required': '✅' if prop_name in required_fields else '❌',
                    'description': get_description(prop),
                    'examples': get_examples(prop),
                    'format': prop.get('format', '') if prop else ''
                })
        
        schemas_data.append(schema_data)
    
    template = env.get_template('schemas.md.j2')
    # Передаем spec в шаблон
    return template.render(schemas=schemas_data, spec=spec)

def generate_markdown(spec, endpoints_filter=None, include_all_schemas=False):
    """Генерирует Markdown документацию из OpenAPI-спецификации"""
    # Подготовка данных для основного шаблона
    context = {
        'title': spec['info']['title'],
        'version': spec['info']['version'],
        'description': spec['info'].get('description', ''),
        'endpoints_by_tag': defaultdict(list),
        'schemas_section': '',
        'spec': spec  # Ключевое исправление: передаем spec в основной шаблон
    }
    
    # Собираем все используемые схемы
    used_schemas = set() if not include_all_schemas else None
    
    # Группировка эндпоинтов по тегам
    for path, methods in spec['paths'].items():
        for method, details in methods.items():
            if method.lower() not in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']:
                continue
            
            # Проверка фильтра эндпоинтов
            include_endpoint = True
            if endpoints_filter:
                include_endpoint = (method.upper(), path) in endpoints_filter
            
            if include_endpoint:
                tags = details.get('tags', ['Без тега'])
                for tag in tags:
                    endpoint_data = {
                        'path': path,
                        'method': method.upper(),
                        'details': details,
                        'parameters_table': generate_parameters_table(details.get('parameters', []), spec),
                        'request_body': generate_request_body(details.get('requestBody', {}), spec) if 'requestBody' in details else "",
                        'responses': generate_responses(details.get('responses', {}), spec) if 'responses' in details else ""
                    }
                    context['endpoints_by_tag'][tag].append(endpoint_data)
                
                # Сбор схем
                if not include_all_schemas:
                    for param in details.get('parameters', []):
                        collect_used_schemas(spec, param, used_schemas)
                    if 'requestBody' in details:
                        collect_used_schemas(spec, details['requestBody'], used_schemas)
                    for response in details.get('responses', {}).values():
                        collect_used_schemas(spec, response, used_schemas)
    
    # Генерация секции схем
    context['schemas_section'] = generate_schemas(spec, used_schemas)
    
    # Рендеринг основного шаблона
    template = env.get_template('base.md.j2')
    return template.render(context)