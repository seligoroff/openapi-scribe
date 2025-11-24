"""Use case для получения списка всех эндпоинтов"""
from typing import List
from ports.spec_loader import SpecLoader
from domain.models import Endpoint
from domain.services import EndpointFinder


class ListEndpointsUseCase:
    """
    Use case для получения списка всех эндпоинтов из OpenAPI спецификации.
    
    Координирует работу SpecLoader и EndpointFinder для получения списка эндпоинтов.
    """
    
    def __init__(self, spec_loader: SpecLoader):
        """
        Инициализирует use case.
        
        Args:
            spec_loader: Адаптер для загрузки спецификаций
        """
        self.spec_loader = spec_loader
        self.finder = EndpointFinder()
    
    def execute(self, spec_source: str) -> List[Endpoint]:
        """
        Выполняет получение списка всех эндпоинтов из спецификации.
        
        Args:
            spec_source: Путь к файлу спецификации
            
        Returns:
            Список всех эндпоинтов
            
        Raises:
            FileNotFoundError: Если файл спецификации не найден
            IOError: Если произошла ошибка при чтении файла
        """
        # Загрузка спецификации
        spec = self.spec_loader.load(spec_source)
        
        # Получение списка эндпоинтов
        return self.finder.list_all(spec)

