"""Адаптер для загрузки OpenAPI спецификаций из файла"""
import os
import json
from pathlib import Path
from typing import Dict
from ports.spec_loader import SpecLoader
from domain.models import OpenAPISpec


class FileSpecLoader(SpecLoader):
    """
    Адаптер для загрузки OpenAPI спецификаций из файла.
    
    Мигрировано из oatools/utils.py::load_openapi_spec().
    """
    
    def load(self, source: str) -> OpenAPISpec:
        """
        Загружает OpenAPI спецификацию из файла.
        
        Args:
            source: Путь к файлу спецификации
            
        Returns:
            OpenAPISpec instance
            
        Raises:
            FileNotFoundError: Если файл не найден
            ValueError: Если JSON невалиден
            IOError: Если произошла ошибка при чтении файла
        """
        # Расширение пути с тильдой
        expanded_spec = os.path.expanduser(source)
        
        # Разрешение реального пути (убирает символические ссылки)
        resolved_spec = os.path.realpath(expanded_spec)
        spec_path_obj = Path(resolved_spec)
        
        # Проверка существования файла
        if not spec_path_obj.exists():
            raise FileNotFoundError(f"Файл спецификации не найден: {resolved_spec}")
        
        # Чтение и парсинг JSON
        try:
            with open(spec_path_obj, 'r', encoding='utf-8') as f:
                spec_dict = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Невалидный JSON в файле {resolved_spec}: {e}")
        except IOError as e:
            raise IOError(f"Ошибка чтения файла {resolved_spec}: {e}")
        
        # Создание OpenAPISpec из словаря
        return OpenAPISpec.from_dict(spec_dict)

