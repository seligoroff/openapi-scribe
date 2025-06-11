import os
import json
from pathlib import Path

def load_openapi_spec(spec_path):
    """Загружает и валидирует OpenAPI спецификацию"""
    expanded_spec = os.path.expanduser(spec_path)
    resolved_spec = os.path.realpath(expanded_spec)
    spec_path_obj = Path(resolved_spec)
    
    if not spec_path_obj.exists():
        raise FileNotFoundError(f"Файл спецификации не найден: {resolved_spec}")

    with open(spec_path_obj, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_endpoints_filter(file_path):
    """Загружает список эндпоинтов для фильтрации из файла"""
    endpoints = set()
    try:
        if file_path:
            expanded_path = os.path.expanduser(file_path)
            with open(expanded_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split(maxsplit=1)
                        if len(parts) == 2:
                            method, path = parts
                            endpoints.add((method.upper(), path))
                        else:
                            print(f"⚠️ Пропущена некорректная строка: {line}")
    except FileNotFoundError:
        raise FileNotFoundError(f"Файл фильтра {file_path} не найден")
    return endpoints

def resolve_ref(spec, ref, resolve_depth=0):
    """
    Разрешает $ref ссылки в OpenAPI-спецификации
    с защитой от бесконечной рекурсии и кешированием
    """
    if resolve_depth > 10:
        return {}
    
    # Кеширование результатов
    if not hasattr(resolve_ref, 'cache'):
        resolve_ref.cache = {}
    
    if ref in resolve_ref.cache:
        return resolve_ref.cache[ref]
    
    if ref.startswith('#/components/parameters/'):
        param_name = ref.split('/')[-1]
        resolved = spec.get('components', {}).get('parameters', {}).get(param_name, {})
        resolve_ref.cache[ref] = resolved
        return resolved
    
    if ref.startswith('#/components/schemas/'):
        schema_name = ref.split('/')[-1]
        schema = spec.get('components', {}).get('schemas', {}).get(schema_name, {})
        
        # Рекурсивно разрешаем вложенные ссылки
        if isinstance(schema, dict) and '$ref' in schema:
            resolved = resolve_ref(spec, schema['$ref'], resolve_depth + 1)
            resolve_ref.cache[ref] = resolved
            return resolved
        
        resolve_ref.cache[ref] = schema
        return schema
    
    # Обработка других типов ссылок
    if ref.startswith('#'):
        parts = ref.split('/')[1:]
        current = spec
        for part in parts:
            if part in current:
                current = current[part]
            else:
                break
        if current != spec:
            resolve_ref.cache[ref] = current
            return current
    
    resolve_ref.cache[ref] = {}
    return {}

def process_schema(spec, node, depth=0):
    """
    Рекурсивно обрабатывает схему данных, включая разрешение ссылок
    и обработку вложенных структур с защитой от глубокой рекурсии
    """
    if depth > 10:  # Увеличена глубина рекурсии
        return node
    
    if isinstance(node, dict):
        # Обработка ссылок
        if '$ref' in node:
            resolved = resolve_ref(spec, node['$ref'])
            if resolved:
                # Сохраняем другие свойства вместе с разрешенной ссылкой
                new_node = {**resolved, **{k: v for k, v in node.items() if k != '$ref'}}
                # Сохраняем оригинальную ссылку
                new_node['x-original-ref'] = node['$ref']
                return process_schema(spec, new_node, depth + 1)
        
        # Рекурсивная обработка вложенных элементов
        processed = {}
        for key, value in node.items():
            processed[key] = process_schema(spec, value, depth + 1)
        return processed
    
    elif isinstance(node, list):
        return [process_schema(spec, item, depth + 1) for item in node]
    
    return node