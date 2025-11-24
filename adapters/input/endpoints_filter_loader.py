"""Адаптер для загрузки фильтра эндпоинтов из файла"""
import os
from typing import Set, Tuple


def load_endpoints_filter(file_path: str) -> Set[Tuple[str, str]]:
    """
    Загружает список эндпоинтов для фильтрации из файла.
    
    Формат файла: каждая строка содержит метод и путь, разделенные пробелом.
    Строки, начинающиеся с #, игнорируются как комментарии.
    
    Args:
        file_path: Путь к файлу с фильтром эндпоинтов
        
    Returns:
        Множество кортежей (method, path)
        
    Raises:
        FileNotFoundError: Если файл не найден
    """
    endpoints = set()
    if not file_path:
        return endpoints
    
    expanded_path = os.path.expanduser(file_path)
    
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

