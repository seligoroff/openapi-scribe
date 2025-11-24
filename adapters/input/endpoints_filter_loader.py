"""Адаптер для загрузки фильтра эндпоинтов из файла"""
import os
from typing import Set, Tuple
from ports.endpoints_filter_loader import EndpointsFilterLoader


class FileEndpointsFilterLoader(EndpointsFilterLoader):
    """
    Адаптер для загрузки фильтра эндпоинтов из файла.
    
    Формат файла: каждая строка содержит метод и путь, разделенные пробелом.
    Строки, начинающиеся с #, игнорируются как комментарии.
    """
    
    def load(self, source: str) -> Set[Tuple[str, str]]:
        """
        Загружает список эндпоинтов для фильтрации из файла.
        
        Args:
            source: Путь к файлу с фильтром эндпоинтов
            
        Returns:
            Множество кортежей (method, path)
            
        Raises:
            FileNotFoundError: Если файл не найден
            IOError: Если произошла ошибка при чтении файла
        """
        endpoints = set()
        if not source:
            return endpoints
        
        expanded_path = os.path.expanduser(source)
        
        if not os.path.exists(expanded_path):
            raise FileNotFoundError(f"Файл фильтра {expanded_path} не найден")
        
        with open(expanded_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split(maxsplit=1)
                    if len(parts) == 2:
                        method, path = parts
                        endpoints.add((method.upper(), path))
                    # Игнорируем некорректные строки без вывода предупреждения
        
        return endpoints


# Функция для обратной совместимости (legacy)
def load_endpoints_filter(file_path: str) -> Set[Tuple[str, str]]:
    """
    Загружает список эндпоинтов для фильтрации из файла.
    
    Устаревшая функция, используйте FileEndpointsFilterLoader вместо неё.
    
    Args:
        file_path: Путь к файлу с фильтром эндпоинтов
        
    Returns:
        Множество кортежей (method, path)
        
    Raises:
        FileNotFoundError: Если файл не найден
    """
    loader = FileEndpointsFilterLoader()
    return loader.load(file_path)

