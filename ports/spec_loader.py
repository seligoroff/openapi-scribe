"""Порт для загрузки OpenAPI спецификаций"""
from abc import ABC, abstractmethod
from domain.models import OpenAPISpec


class SpecLoader(ABC):
    """
    Абстрактный порт для загрузки OpenAPI спецификаций из различных источников.
    
    Этот интерфейс позволяет абстрагироваться от конкретной реализации загрузки,
    что упрощает тестирование и позволяет легко добавлять новые источники данных
    (файлы, URL, база данных и т.д.).
    """
    
    @abstractmethod
    def load(self, source: str) -> OpenAPISpec:
        """
        Загружает OpenAPI спецификацию из источника.
        
        Args:
            source: Путь к источнику спецификации (файл, URL и т.д.)
            
        Returns:
            OpenAPISpec instance
            
        Raises:
            FileNotFoundError: Если источник не найден
            ValueError: Если спецификация невалидна
            IOError: Если произошла ошибка при чтении
        """
        pass

