"""Use case для получения информации об эндпоинте"""
from typing import Optional
from ports.spec_loader import SpecLoader
from domain.models import Endpoint
from domain.services import EndpointFinder


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
    
    def execute(self, spec_source: str, path: str, method: str) -> Optional[Endpoint]:
        """
        Выполняет поиск эндпоинта в спецификации.
        
        Args:
            spec_source: Путь к файлу спецификации
            path: Путь эндпоинта
            method: HTTP метод
            
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

