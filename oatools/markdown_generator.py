import json
from collections import defaultdict
from .utils import process_schema, resolve_ref

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
    return node.get('description') or node.get('title', '')

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
                if 'value' in example_data:
                    summary = example_data.get('summary', name)
                    examples.append((summary, example_data['value']))
                elif isinstance(example_data, dict) and 'value' not in example_data:
                    # Обработка случая, когда пример представлен напрямую
                    examples.append((name, example_data))
        elif isinstance(node['examples'], list) and node['examples']:
            for i, example in enumerate(node['examples']):
                examples.append((f"Пример {i+1}", example))
    
    return examples

def format_example(example, max_length=100):
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
    """Генерирует таблицу параметров с улучшенной обработкой примеров"""
    if not parameters:
        return ""
    
    headers = [
        "Имя", "Тип", "Расположение", "Обязательный", 
        "Описание", "Примеры", "Формат"
    ]
    table = [
        f"| {' | '.join(headers)} |",
        f"|{'-:|' * len(headers)}"
    ]
    
    for param in parameters:
        # Обработка ссылок
        resolved_param = param.copy()
        if 'schema' in param:
            resolved_param['schema'] = process_schema(spec, param['schema'])
        
        # Форматирование типа
        param_type = format_type(resolved_param['schema'])
        
        # Извлечение ВСЕХ примеров
        examples = get_examples(resolved_param)
        example_str = ""
        if examples:
            example_str = "<br>".join(
                f"**{name}:** `{format_example(ex, 50)}`" 
                for name, ex in examples
            )
        
        # Форматирование описания с HTML-переносами
        description = get_description(resolved_param)
        if description:
            description = description.replace('\n', '<br>').replace('  - ', '<br>- ')
        
        row = [
            f"`{resolved_param['name']}`",
            param_type,
            resolved_param['in'],
            "✅" if resolved_param.get('required', False) else "❌",
            description or "",
            example_str,
            resolved_param.get('schema', {}).get('format', '')
        ]
        table.append("| " + " | ".join(row) + " |")
    
    return "\n".join(table)

def generate_request_body(body, spec):
    """Генерирует описание тела запроса с улучшенной обработкой схем"""
    if not body:
        return ""
    
    result = ["**Тело запроса:**"]
    
    # Добавлено описание тела
    if 'description' in body:
        desc = body['description'].replace('\n', '  \n')
        result.append(f"**Описание:** {desc}")
    
    for content_type, media in body.get('content', {}).items():
        result.append(f"- **Тип контента:** `{content_type}`")
        
        if 'schema' in media:
            original_schema = media['schema']
            schema = process_schema(spec, original_schema)
            
            # Вывод информации о схеме
            if '$ref' in original_schema:
                ref_name = original_schema['$ref'].split('/')[-1]
                # Пытаемся получить заголовок схемы
                title = ""
                try:
                    ref_schema = resolve_ref(spec, original_schema['$ref'])
                    title = ref_schema.get('title', '')
                except Exception:
                    pass
                display_name = title or ref_name
                result.append(f"- **Схема:** [{display_name}](#{ref_name.lower()})")
            else:
                result.append(f"- **Тип:** {format_type(schema)}")
            
            # Генерация таблицы свойств
            if schema.get('type') == 'object' and 'properties' in schema:
                result.append("**Свойства:**")
                required_fields = schema.get('required', [])
                
                props_table = [
                    "| Имя | Тип | Обязательный | Описание | Примеры | Формат |",
                    "|-----|-----|--------------|----------|---------|--------|"
                ]
                
                for prop_name, prop in schema['properties'].items():
                    # Обработка вложенных ссылок и типов
                    prop = process_schema(spec, prop)
                    
                    # Извлечение ВСЕХ примеров
                    examples = get_examples(prop)
                    example_str = ""
                    if examples:
                        example_str = "<br>".join(
                            f"**{name}:** `{format_example(ex, 30)}`" 
                            for name, ex in examples
                        )
                    
                    # Форматирование описания с HTML-переносами
                    description = get_description(prop)
                    if description:
                        description = description.replace('\n', '<br>').replace('  - ', '<br>- ')
                    
                    props_table.append(
                        f"| `{prop_name}` | {format_type(prop)} | "
                        f"{'✅' if prop_name in required_fields else '❌'} | "
                        f"{description or ''} | "
                        f"{example_str} | "
                        f"{prop.get('format', '')} |"
                    )
                
                result.append("\n".join(props_table))
        
        # Добавлена обработка примеров
        examples = get_examples(media)
        if examples:
            for name, example in examples:
                example_str = format_example(example, 200)
                result.append(f"- **Пример ({name}):**\n```json\n{example_str}\n```")
    
    return "\n".join(result)

def generate_responses(responses, spec):
    """Генерирует описание ответов с улучшенной детализацией"""
    if not responses:
        return ""
    
    result = ["**Ответы:**"]
    for code, response in responses.items():
        # Форматирование описания с переносами
        description = response.get('description', '')
        if description:
            description = description.replace('\n', '  \n')
        result.append(f"##### **Код {code}:** {description}")
        
        for content_type, media in response.get('content', {}).items():
            result.append(f"  - **Тип контента:** `{content_type}`")
            
            if 'schema' in media:
                schema = media['schema']
                schema_type = format_type(schema)
                
                if '$ref' in schema:
                    ref_name = schema['$ref'].split('/')[-1]
                    # Получаем заголовок схемы из компонентов
                    title = ""
                    try:
                        schema_ref = resolve_ref(spec, schema['$ref'])
                        title = schema_ref.get('title', '')
                    except Exception:
                        pass
                    display_name = title or ref_name
                    result.append(f"  - **Схема:** [{display_name}](#{ref_name.lower()})")
                else:
                    result.append(f"  - **Тип:** {schema_type}")
            
            # Добавлена обработка примеров
            examples = get_examples(media)
            if examples:
                for name, example in examples:
                    example_str = format_example(example)
                    result.append(f"###### **Пример ({name}):**\n```json\n{example_str}\n```")
    
    return "\n".join(result)

def generate_schemas(spec, used_schemas=None):
    """Генерирует раздел со схемами данных с полной информацией"""
    schemas = spec.get('components', {}).get('schemas', {})
    if not schemas:
        return ""
    
    # Фильтрация схем
    if used_schemas is not None:
        schemas = {name: schema for name, schema in schemas.items() if name in used_schemas}
    
    if not schemas:
        return ""
    
    result = ["---", "## 📖 Схемы данных"]
    for name, schema in schemas.items():
        result.append(f"### {name}")
        
        # Вывод заголовка схемы
        if 'title' in schema:
            result.append(f" - **Название:** {schema['title']}")
        
        # Тип схемы
        result.append(f" - **Тип:** `{schema.get('type', 'object')}`")
        
        # Описание схемы
        if 'description' in schema:
            description = schema['description']
            if description:
                description = description.replace('\n', '  \n')
            result.append(f" - **Описание:** {description}")
        
        # Вывод обязательных полей
        if 'required' in schema:
            result.append(f" - **Обязательные поля:** `{', '.join(schema['required'])}`")
        
        if 'properties' in schema:
            result.append("#### **Свойства:**")
            props_table = [
                "| Имя | Тип | Обязательный | Описание | Примеры | Формат |",
                "|-----|-----|--------------|----------|---------|--------|"
            ]
            
            required_fields = schema.get('required', [])
            
            for prop_name, prop in schema['properties'].items():
                # Обработка вложенных ссылок и типов
                prop = process_schema(spec, prop)
                
                # Извлечение ВСЕХ примеров
                examples = get_examples(prop)
                example_str = ""
                if examples:
                    example_str = "<br>".join(
                        f"**{name}:** `{format_example(ex, 30)}`" 
                        for name, ex in examples
                    )
                
                # Форматирование описания с HTML-переносами
                description = get_description(prop)
                if description:
                    description = description.replace('\n', '<br>').replace('  - ', '<br>- ')
                
                props_table.append(
                    f"| `{prop_name}` | {format_type(prop)} | "
                    f"{'✅' if prop_name in required_fields else '❌'} | "
                    f"{description or ''} | "
                    f"{example_str} | "
                    f"{prop.get('format', '')} |"
                )
            
            result.append("\n".join(props_table))
        
        # Вывод примера всей схемы
        if 'example' in schema:
            example = schema['example']
            if isinstance(example, dict):
                example_str = json.dumps(example, indent=2, ensure_ascii=False)
                result.append(f"**Пример:**\n```json\n{example_str}\n```")
            elif example:
                result.append(f"**Пример:**\n```\n{example}\n```")
        
        result.append("")
    
    return "\n".join(result)

def generate_markdown(spec, endpoints_filter=None, include_all_schemas=False):
    """Генерирует Markdown документацию из OpenAPI-спецификации"""
    output = [
        f"# {spec['info']['title']}",
        f"**Версия:** {spec['info']['version']}",
        f"**Описание:** {spec['info'].get('description', '')}",
        "---",
        "## 🚀 Эндпоинты"
    ]
    
    # Собираем все используемые схемы
    used_schemas = set() if not include_all_schemas else None
    
    # Группировка эндпоинтов по тегам
    endpoints_by_tag = defaultdict(list)
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
                    endpoints_by_tag[tag].append((path, method, details))
                
                # Сбор схем из параметров (если не включены все схемы)
                if not include_all_schemas:
                    for param in details.get('parameters', []):
                        collect_used_schemas(spec, param, used_schemas)
                    
                    # Сбор схем из тела запроса
                    if 'requestBody' in details:
                        collect_used_schemas(spec, details['requestBody'], used_schemas)
                    
                    # Сбор схем из ответов
                    for response in details.get('responses', {}).values():
                        collect_used_schemas(spec, response, used_schemas)
    
    # Генерация документации по тегам
    for tag, endpoints in endpoints_by_tag.items():
        output.append(f"### {tag}")
        
        for path, method, details in endpoints:
            # Заголовок эндпоинта
            output.append(f"#### `{method.upper()}` {path}")
            if details.get('deprecated', False):
                output.append("> ⚠️ **Устарел**")
            
            # Вывод operationId
            if 'operationId' in details:
                output.append(f"**ID операции:** `{details['operationId']}`")
            
            # Улучшенное описание (summary + description)
            summary = details.get('summary', '')
            description = details.get('description', '')
            
            if summary and description:
                output.append(f"**Описание:** {summary}  \n{description}")
            elif summary:
                output.append(f"**Описание:** {summary}")
            elif description:
                output.append(f"**Описание:** {description}")
            
            # Параметры
            params = details.get('parameters', [])
            if params:
                output.append(generate_parameters_table(params, spec))
            
            # Тело запроса
            request_body = details.get('requestBody', {})
            if request_body:
                output.append(generate_request_body(request_body, spec))
            
            # Ответы
            responses = details.get('responses', {})
            if responses:
                output.append(generate_responses(responses, spec))
            
            output.append("---")
    
    # Схемы данных
    schemas_section = generate_schemas(spec, used_schemas)
    if schemas_section:
        output.append(schemas_section)
    
    return "\n\n".join(output)