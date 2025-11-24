"""Use case для получения информации о схеме"""
from typing import Optional
from ports.spec_loader import SpecLoader
from domain.models import Schema


class GetSchemaInfoUseCase:
    """
    Use case для получения информации о схеме данных из OpenAPI спецификации.
    
    Координирует работу SpecLoader для поиска схемы.
    """
    
    def __init__(self, spec_loader: SpecLoader):
        """
        Инициализирует use case.
        
        Args:
            spec_loader: Адаптер для загрузки спецификаций
        """
        self.spec_loader = spec_loader
    
    def execute(self, spec_source: str, schema_name: str) -> Optional[Schema]:
        """
        Выполняет поиск схемы в спецификации.
        
        Args:
            spec_source: Путь к файлу спецификации
            schema_name: Имя схемы для поиска
            
        Returns:
            Schema если найдена, None иначе
            
        Raises:
            FileNotFoundError: Если файл спецификации не найден
            ValueError: Если схема не найдена
            IOError: Если произошла ошибка при чтении файла
        """
        # Загрузка спецификации
        spec = self.spec_loader.load(spec_source)
        
        # Поиск схемы
        schema_definition = spec.schemas.get(schema_name)
        
        if not schema_definition:
            return None
        
        return Schema(name=schema_name, definition=schema_definition)

