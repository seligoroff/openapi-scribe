"""Use case для генерации Markdown документации"""
from typing import Optional
from ports.spec_loader import SpecLoader
from domain.models import EndpointFilter
from rendering.markdown import MarkdownGenerator
from adapters.input.endpoints_filter_loader import load_endpoints_filter


class GenerateDocumentationUseCase:
    """
    Use case для генерации Markdown документации из OpenAPI спецификации.
    
    Координирует работу SpecLoader и MarkdownGenerator для генерации документации.
    """
    
    def __init__(self, spec_loader: SpecLoader):
        """
        Инициализирует use case.
        
        Args:
            spec_loader: Адаптер для загрузки спецификаций
        """
        self.spec_loader = spec_loader
        self.markdown_generator = MarkdownGenerator()
    
    def execute(
        self,
        spec_source: str,
        endpoints_filter: Optional[str] = None,
        include_all_schemas: bool = False
    ) -> str:
        """
        Выполняет генерацию Markdown документации.
        
        Args:
            spec_source: Путь к файлу спецификации
            endpoints_filter: Путь к файлу с фильтром эндпоинтов (опционально)
            include_all_schemas: Включить все схемы, а не только используемые
            
        Returns:
            Сгенерированная Markdown документация
            
        Raises:
            FileNotFoundError: Если файл спецификации не найден
            IOError: Если произошла ошибка при чтении файла
        """
        # Загрузка спецификации
        spec_obj = self.spec_loader.load(spec_source)
        
        # Загрузка фильтра эндпоинтов
        endpoint_filter: Optional[EndpointFilter] = None
        if endpoints_filter:
            try:
                filter_set = load_endpoints_filter(endpoints_filter)
                endpoint_filter = EndpointFilter.from_set(filter_set)
            except FileNotFoundError:
                # Если файл фильтра не найден, продолжаем без фильтра
                endpoint_filter = None
        
        # Генерация документации через новый MarkdownGenerator
        return self.markdown_generator.generate(
            spec=spec_obj,
            endpoints_filter=endpoint_filter,
            include_all_schemas=include_all_schemas
        )

