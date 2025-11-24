"""Порт для загрузки фильтра эндпоинтов"""
from abc import ABC, abstractmethod
from typing import Set, Tuple


class EndpointsFilterLoader(ABC):
    """
    Абстрактный порт для загрузки фильтра эндпоинтов из различных источников.
    
    Позволяет загружать фильтры эндпоинтов из файлов, баз данных, API и т.д.
    """
    
    @abstractmethod
    def load(self, source: str) -> Set[Tuple[str, str]]:
        """
        Загружает фильтр эндпоинтов из источника.
        
        Args:
            source: Источник фильтра (путь к файлу, URL, идентификатор и т.д.)
            
        Returns:
            Множество кортежей (method, path) для фильтрации
            
        Raises:
            FileNotFoundError: Если источник не найден
            IOError: Если произошла ошибка при чтении источника
        """
        pass

