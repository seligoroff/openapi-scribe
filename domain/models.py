"""Value objects для доменной модели"""
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Optional


@dataclass(frozen=True)
class OpenAPISpec:
    """
    Value object для представления OpenAPI спецификации.
    
    Attributes:
        raw: Полный словарь спецификации
        paths: Секция paths из спецификации
        schemas: Секция components/schemas из спецификации
        info: Секция info из спецификации
    """
    raw: Dict
    paths: Dict
    schemas: Dict
    info: Dict
    
    @classmethod
    def from_dict(cls, spec_dict: Dict) -> 'OpenAPISpec':
        """
        Создает OpenAPISpec из словаря OpenAPI спецификации.
        
        Args:
            spec_dict: Словарь с OpenAPI спецификацией
            
        Returns:
            OpenAPISpec instance
        """
        return cls(
            raw=spec_dict,
            paths=spec_dict.get('paths', {}),
            schemas=spec_dict.get('components', {}).get('schemas', {}),
            info=spec_dict.get('info', {})
        )


@dataclass(frozen=True)
class Endpoint:
    """
    Value object для представления эндпоинта API.
    
    Attributes:
        path: Путь эндпоинта (например, "/api/v1/users")
        method: HTTP метод (например, "GET", "POST")
        operation: Словарь с данными операции из спецификации
        tags: Список тегов операции
    """
    path: str
    method: str
    operation: Dict
    tags: List[str]
    
    def __post_init__(self):
        """Нормализует метод к верхнему регистру"""
        object.__setattr__(self, 'method', self.method.upper())


@dataclass(frozen=True)
class Schema:
    """
    Value object для представления схемы данных.
    
    Attributes:
        name: Имя схемы
        definition: Определение схемы из спецификации
    """
    name: str
    definition: Dict


@dataclass(frozen=True)
class EndpointFilter:
    """
    Value object для фильтрации эндпоинтов.
    
    Attributes:
        endpoints: Множество кортежей (method, path) для фильтрации
    """
    endpoints: Set[Tuple[str, str]]
    
    def matches(self, method: str, path: str) -> bool:
        """
        Проверяет, соответствует ли эндпоинт фильтру.
        
        Args:
            method: HTTP метод
            path: Путь эндпоинта
            
        Returns:
            True если эндпоинт соответствует фильтру, False иначе
        """
        normalized_method = method.upper()
        normalized_path = path.rstrip('/')
        
        # Проверяем точное совпадение
        if (normalized_method, normalized_path) in self.endpoints:
            return True
        
        # Проверяем вариант с trailing slash
        if (normalized_method, normalized_path + '/') in self.endpoints:
            return True
        
        return False
    
    @classmethod
    def from_set(cls, endpoints: Set[Tuple[str, str]]) -> 'EndpointFilter':
        """
        Создает EndpointFilter из множества кортежей.
        
        Args:
            endpoints: Множество кортежей (method, path)
            
        Returns:
            EndpointFilter instance
        """
        # Нормализуем методы к верхнему регистру
        normalized = {(method.upper(), path) for method, path in endpoints}
        return cls(endpoints=normalized)
    
    @classmethod
    def empty(cls) -> 'EndpointFilter':
        """
        Создает пустой фильтр (не фильтрует ничего).
        
        Returns:
            EndpointFilter с пустым множеством
        """
        return cls(endpoints=set())
