"""Доменные сервисы"""
from typing import Dict, List, Optional, Set
from .models import OpenAPISpec, Endpoint


class EndpointFinder:
    """
    Сервис для поиска эндпоинтов в OpenAPI спецификации.
    
    Мигрировано из cli.py (команда endpoint).
    """
    
    @staticmethod
    def find(spec: OpenAPISpec, path: str, method: str) -> Optional[Endpoint]:
        """
        Находит эндпоинт по пути и методу.
        
        Args:
            spec: OpenAPI спецификация
            path: Путь эндпоинта
            method: HTTP метод
            
        Returns:
            Endpoint если найден, None иначе
            
        Raises:
            ValueError: Если путь или метод не найдены
        """
        # Нормализация URL (удаление trailing slash)
        endpoint_path = path.rstrip('/')
        
        # Поиск совпадения по URL
        exact_match = spec.paths.get(endpoint_path)
        
        if not exact_match:
            # Попытка найти вариант с trailing slash
            alt_path = endpoint_path + '/'
            exact_match = spec.paths.get(alt_path)
            if exact_match:
                endpoint_path = alt_path
        
        if not exact_match:
            raise ValueError(f"Путь '{path}' не найден в спецификации")
        
        # Проверка метода
        method_lower = method.lower()
        endpoint_info = exact_match.get(method_lower)
        
        if not endpoint_info:
            available_methods = [m.upper() for m in exact_match.keys() 
                               if m.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']]
            raise ValueError(
                f"Метод {method.upper()} не найден. Доступные методы: {', '.join(available_methods)}"
            )
        
        # Извлечение тегов
        tags = endpoint_info.get('tags', ['Без тега'])
        
        return Endpoint(
            path=endpoint_path,
            method=method,
            operation=endpoint_info,
            tags=tags
        )
    
    @staticmethod
    def list_all(spec: OpenAPISpec) -> List[Endpoint]:
        """
        Возвращает список всех эндпоинтов из спецификации.
        
        Args:
            spec: OpenAPI спецификация
            
        Returns:
            Список всех эндпоинтов
        """
        endpoints = []
        
        for path, methods in spec.paths.items():
            for method, operation in methods.items():
                # Фильтрация только стандартных HTTP методов
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
                    tags = operation.get('tags', ['Без тега'])
                    endpoints.append(Endpoint(
                        path=path,
                        method=method,
                        operation=operation,
                        tags=tags
                    ))
        
        return endpoints


class SchemaResolver:
    """
    Сервис для разрешения $ref ссылок и обработки схем.
    
    Мигрировано из utils.py (resolve_ref, process_schema).
    """
    
    def __init__(self, spec: OpenAPISpec):
        """
        Инициализирует резолвер схем.
        
        Args:
            spec: OpenAPI спецификация
        """
        self.spec = spec
        self._cache: Dict[str, Dict] = {}
    
    def resolve(self, ref: str, depth: int = 0) -> Optional[Dict]:
        """
        Разрешает $ref ссылки в OpenAPI-спецификации
        с защитой от бесконечной рекурсии и кешированием.
        
        Args:
            ref: Ссылка вида "#/components/schemas/User"
            depth: Глубина рекурсии (для защиты от бесконечной рекурсии)
            
        Returns:
            Разрешенная схема или None
        """
        if depth > 10:
            return {}
        
        # Проверка кеша
        if ref in self._cache:
            return self._cache[ref]
        
        # Обработка параметров
        if ref.startswith('#/components/parameters/'):
            param_name = ref.split('/')[-1]
            resolved = self.spec.raw.get('components', {}).get('parameters', {}).get(param_name, {})
            self._cache[ref] = resolved
            return resolved
        
        # Обработка схем
        if ref.startswith('#/components/schemas/'):
            schema_name = ref.split('/')[-1]
            schema = self.spec.schemas.get(schema_name, {})
            
            # Рекурсивно разрешаем вложенные ссылки
            if isinstance(schema, dict) and '$ref' in schema:
                resolved = self.resolve(schema['$ref'], depth + 1)
                self._cache[ref] = resolved
                return resolved
            
            self._cache[ref] = schema
            return schema
        
        # Обработка других типов ссылок
        if ref.startswith('#'):
            parts = ref.split('/')[1:]
            current = self.spec.raw
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    break
            if current != self.spec.raw:
                self._cache[ref] = current if isinstance(current, dict) else {}
                return current if isinstance(current, dict) else {}
        
        self._cache[ref] = {}
        return {}
    
    def process_schema(self, node: Dict, depth: int = 0) -> Dict:
        """
        Рекурсивно обрабатывает схему данных, включая разрешение ссылок
        и обработку вложенных структур с защитой от глубокой рекурсии.
        
        Args:
            node: Узел схемы для обработки
            depth: Глубина рекурсии
            
        Returns:
            Обработанная схема
        """
        if depth > 10:
            return node
        
        if isinstance(node, dict):
            # Обработка ссылок
            if '$ref' in node:
                resolved = self.resolve(node['$ref'])
                if resolved:
                    # Сохраняем другие свойства вместе с разрешенной ссылкой
                    new_node = {**resolved, **{k: v for k, v in node.items() if k != '$ref'}}
                    # Сохраняем оригинальную ссылку
                    new_node['x-original-ref'] = node['$ref']
                    return self.process_schema(new_node, depth + 1)
            
            # Рекурсивная обработка вложенных элементов
            processed = {}
            for key, value in node.items():
                processed[key] = self.process_schema(value, depth + 1) if isinstance(value, (dict, list)) else value
            return processed
        
        elif isinstance(node, list):
            return [self.process_schema(item, depth + 1) if isinstance(item, (dict, list)) else item for item in node]
        
        return node
    
    def clear_cache(self):
        """Очищает кеш резолвера"""
        self._cache.clear()


class SchemaCollector:
    """
    Сервис для сбора используемых схем из эндпоинта.
    
    Мигрировано из markdown_generator.py (collect_used_schemas).
    """
    
    def __init__(self, spec: OpenAPISpec, resolver: SchemaResolver):
        """
        Инициализирует коллектор схем.
        
        Args:
            spec: OpenAPI спецификация
            resolver: Резолвер схем для разрешения ссылок
        """
        self.spec = spec
        self.resolver = resolver
    
    def collect_from_endpoint(self, endpoint: Endpoint) -> Set[str]:
        """
        Собирает все использованные схемы из эндпоинта.
        
        Args:
            endpoint: Эндпоинт для анализа
            
        Returns:
            Множество имен используемых схем
        """
        collected: Set[str] = set()
        
        # Собираем схемы из параметров
        for param in endpoint.operation.get('parameters', []):
            self._collect_from_node(param, collected)
        
        # Собираем схемы из тела запроса
        if 'requestBody' in endpoint.operation:
            self._collect_from_node(endpoint.operation['requestBody'], collected)
        
        # Собираем схемы из ответов
        for response in endpoint.operation.get('responses', {}).values():
            self._collect_from_node(response, collected)
        
        return collected
    
    def _collect_from_node(self, node, collected: Set[str]):
        """
        Рекурсивно собирает схемы из узла спецификации.
        
        Args:
            node: Узел для анализа
            collected: Множество для сбора имен схем
        """
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
                            schema_node = self.resolver.resolve(ref)
                            if schema_node:
                                self._collect_from_node(schema_node, collected)
                        except Exception:
                            pass  # Игнорируем ошибки разрешения ссылок
            
            # Обработка комбинаторов схем
            for key in ['allOf', 'anyOf', 'oneOf']:
                if key in node:
                    for item in node[key]:
                        self._collect_from_node(item, collected)
            
            # Обработка свойств объектов
            if 'properties' in node:
                for prop in node['properties'].values():
                    self._collect_from_node(prop, collected)
            
            # Обработка элементов массивов
            if 'items' in node:
                self._collect_from_node(node['items'], collected)
            
            # Обработка additionalProperties
            if 'additionalProperties' in node and isinstance(node['additionalProperties'], dict):
                self._collect_from_node(node['additionalProperties'], collected)
            
            # Рекурсивный обход
            for key, value in node.items():
                # Пропускаем уже обработанные ключи
                if key in ['$ref', 'allOf', 'anyOf', 'oneOf', 'properties', 'items', 'additionalProperties']:
                    continue
                self._collect_from_node(value, collected)
        
        elif isinstance(node, list):
            for item in node:
                self._collect_from_node(item, collected)
