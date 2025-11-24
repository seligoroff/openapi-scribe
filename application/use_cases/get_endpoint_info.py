"""Use case для получения информации об эндпоинте"""
from typing import Optional, List, Dict
from ports.spec_loader import SpecLoader
from domain.models import Endpoint
from domain.services import EndpointFinder, SchemaResolver


class GetEndpointInfoUseCase:
    """
    Use case для получения информации об эндпоинте из OpenAPI спецификации.
    
    Координирует работу SpecLoader и EndpointFinder для поиска эндпоинта.
    """
    
    def __init__(self, spec_loader: SpecLoader):
        """
        Инициализирует use case.
        
        Args:
            spec_loader: Адаптер для загрузки спецификаций
        """
        self.spec_loader = spec_loader
        self.finder = EndpointFinder()
    
    def execute(self, spec_source: str, path: str, method: str, expand_schemas: bool = False) -> Optional[Endpoint]:
        """
        Выполняет поиск эндпоинта в спецификации.
        
        Args:
            spec_source: Путь к файлу спецификации
            path: Путь эндпоинта
            method: HTTP метод
            expand_schemas: Если True, возвращает также связанные схемы
            
        Returns:
            Endpoint если найден, None иначе
            
        Raises:
            FileNotFoundError: Если файл спецификации не найден
            ValueError: Если путь или метод не найдены
            IOError: Если произошла ошибка при чтении файла
        """
        # Загрузка спецификации
        spec = self.spec_loader.load(spec_source)
        
        # Поиск эндпоинта
        return self.finder.find(spec, path, method)
    
    def get_related_schemas(self, spec_source: str, endpoint: Endpoint) -> List[Dict[str, Dict]]:
        """
        Находит все связанные схемы для эндпоинта.
        
        Args:
            spec_source: Путь к файлу спецификации
            endpoint: Эндпоинт для анализа
            
        Returns:
            Список словарей вида [{"name": "SchemaName", "definition": {...}}, ...]
            
        Raises:
            FileNotFoundError: Если файл спецификации не найден
            IOError: Если произошла ошибка при чтении файла
        """
        # Загрузка спецификации
        spec = self.spec_loader.load(spec_source)
        resolver = SchemaResolver(spec)
        visited_schemas = set()
        related_schemas = []
        
        def find_schemas(node):
            """Рекурсивно находит все схемы в узле"""
            if isinstance(node, dict):
                # Обработка ссылок
                if '$ref' in node:
                    ref = node['$ref']
                    if ref.startswith('#/components/schemas/'):
                        schema_name = ref.split('/')[-1]
                        if schema_name not in visited_schemas:
                            visited_schemas.add(schema_name)
                            resolved_schema = resolver.resolve(ref)
                            if resolved_schema:
                                related_schemas.append({
                                    "name": schema_name,
                                    "definition": resolved_schema
                                })
                                # Рекурсивный обход свойств схемы
                                find_schemas(resolved_schema)
                
                # Рекурсивный обход вложенных элементов
                for key, value in node.items():
                    find_schemas(value)
            
            elif isinstance(node, list):
                for item in node:
                    find_schemas(item)
        
        # Поиск схем в параметрах
        for param in endpoint.operation.get('parameters', []):
            find_schemas(param)
        
        # Поиск схем в теле запроса
        request_body = endpoint.operation.get('requestBody', {})
        find_schemas(request_body)
        
        # Поиск схем в ответах
        responses = endpoint.operation.get('responses', {})
        find_schemas(responses)
        
        return related_schemas

