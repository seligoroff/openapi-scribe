"""Форматтеры для рендеринга документации"""
import json
import re
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
from domain.models import Endpoint


class TypeFormatter:
    """Форматтер для форматирования типов схем"""
    
    @staticmethod
    def format(schema: Dict) -> str:
        """
        Форматирует тип схемы в читаемый формат.
        
        Args:
            schema: Словарь со схемой (может быть обработан через SchemaResolver)
            
        Returns:
            Отформатированная строка типа
        """
        # Проверка сохранённых оригинальных ссылок
        if 'x-original-ref' in schema:
            ref = schema['x-original-ref']
            if ref.startswith('#/components/schemas/'):
                ref_name = ref.split('/')[-1]
                return f"[{ref_name}](#{ref_name.lower()})"
        
        # Обработка обычных ссылок
        if '$ref' in schema:
            ref_name = schema['$ref'].split('/')[-1]
            return f"[{ref_name}](#{ref_name.lower()})"
        
        # Обработка additionalProperties
        if 'additionalProperties' in schema:
            if isinstance(schema['additionalProperties'], dict):
                value_type = TypeFormatter.format(schema['additionalProperties'])
                return f"object<string, {value_type}>"
            return "object"
        
        # Обработка комбинаторов схем
        if 'anyOf' in schema:
            types = [TypeFormatter.format(s) for s in schema['anyOf']]
            return f"anyOf<{' , '.join(types)}>"
        elif 'oneOf' in schema:
            types = [TypeFormatter.format(s) for s in schema['oneOf']]
            return f"oneOf<{' , '.join(types)}>"
        elif 'allOf' in schema:
            types = [TypeFormatter.format(s) for s in schema['allOf']]
            return f"allOf<{' & '.join(types)}>"
        
        # Обработка массивов
        elif schema.get('type') == 'array' and 'items' in schema:
            items_schema = schema['items']
            
            # Рекурсивный вызов для вложенных элементов
            items_type = TypeFormatter.format(items_schema)
            
            # Определение типа элементов
            if 'type' in items_schema:
                base_type = items_schema['type']
            elif 'x-original-ref' in items_schema:
                ref_name = items_schema['x-original-ref'].split('/')[-1]
                base_type = f"[{ref_name}](#{ref_name.lower()})"
            elif '$ref' in items_schema:
                ref_name = items_schema['$ref'].split('/')[-1]
                base_type = f"[{ref_name}](#{ref_name.lower()})"
            else:
                base_type = 'object'
            
            # Форматирование для примитивных типов
            if base_type in ['string', 'integer', 'number', 'boolean']:
                return f"array<{base_type}>"
            
            # Форматирование для сложных типов
            return f"array<{items_type}>"
        
        # Обработка объектов с properties
        elif schema.get('type') == 'object' and 'properties' in schema:
            return "object"
        
        # Базовый тип
        return schema.get('type', 'object')


class DescriptionFormatter:
    """Форматтер для форматирования описаний"""
    
    @staticmethod
    def format(node: Dict) -> str:
        """
        Извлекает описание с fallback на title.
        
        Args:
            node: Узел спецификации (параметр, схема и т.д.)
            
        Returns:
            Описание или пустая строка
        """
        return node.get('description') or node.get('title', '') or ""
    
    @staticmethod
    def safe_replace(s: Optional[str]) -> str:
        """
        Безопасная замена символов с защитой от None.
        
        Args:
            s: Строка для обработки
            
        Returns:
            Обработанная строка или пустая строка
        """
        if s is None:
            return ""
        return s.replace('\n', '<br>').replace('  - ', '<br>- ')


class ExampleFormatter:
    """Форматтер для форматирования примеров"""
    
    @staticmethod
    def format(example, max_length: int = 150) -> str:
        """
        Форматирует пример для вывода.
        
        Args:
            example: Пример для форматирования
            max_length: Максимальная длина строки
            
        Returns:
            Отформатированная строка примера
        """
        if example is None:
            return ""
            
        if isinstance(example, (dict, list)):
            try:
                example_str = json.dumps(example, ensure_ascii=False, indent=2)
                if len(example_str) > max_length:
                    return example_str[:max_length] + "..."
                return example_str
            except TypeError:
                return str(example)
        return str(example)
    
    @staticmethod
    def extract(node: Dict) -> List[Tuple[str, any]]:
        """
        Извлекает все примеры из узла.
        
        Args:
            node: Узел спецификации (параметр, схема и т.д.)
            
        Returns:
            Список кортежей (название, значение)
        """
        examples = []
        
        # Одиночный пример
        if 'example' in node:
            examples.append(('Пример', node['example']))
        
        # Множественные примеры
        if 'examples' in node:
            if isinstance(node['examples'], dict):
                for name, example_data in node['examples'].items():
                    if isinstance(example_data, dict) and 'value' in example_data:
                        summary = example_data.get('summary', name)
                        examples.append((summary, example_data['value']))
                    elif isinstance(example_data, dict) and 'value' not in example_data:
                        # Обработка случая, когда пример представлен напрямую
                        examples.append((name, example_data))
                    else:
                        # Простое значение
                        examples.append((name, example_data))
            elif isinstance(node['examples'], list) and node['examples']:
                for i, example in enumerate(node['examples']):
                    examples.append((f"Пример {i+1}", example))
        
        # Примеры из схемы (для параметров с schema)
        if 'schema' in node and isinstance(node['schema'], dict):
            schema = node['schema']
            if 'example' in schema:
                examples.append(('Пример', schema['example']))
            if 'examples' in schema:
                if isinstance(schema['examples'], dict):
                    for name, example_data in schema['examples'].items():
                        if isinstance(example_data, dict) and 'value' in example_data:
                            summary = example_data.get('summary', name)
                            examples.append((summary, example_data['value']))
                        else:
                            examples.append((name, example_data))
                elif isinstance(schema['examples'], list):
                    for i, example in enumerate(schema['examples']):
                        examples.append((f"Пример {i+1}", example))
        
        return examples


class StatsFormatter:
    """Форматтер для форматирования статистики API"""
    
    @staticmethod
    def calculate_stats(endpoints: List[Endpoint]) -> Dict:
        """
        Вычисляет статистику по эндпоинтам.
        
        Args:
            endpoints: Список эндпоинтов
            
        Returns:
            Словарь со статистикой
        """
        total = len(endpoints)
        unique_paths = len(set(e.path for e in endpoints))
        
        # Статистика по summary
        with_summary = sum(1 for e in endpoints if e.operation.get('summary'))
        summary_percent = (with_summary / total * 100) if total > 0 else 0
        
        # Статистика по тегам
        without_tags = sum(1 for e in endpoints if not e.tags)
        without_tags_percent = (without_tags / total * 100) if total > 0 else 0
        
        # Статистика по методам HTTP
        methods_count = defaultdict(int)
        for e in endpoints:
            methods_count[e.method] += 1
        
        # Статистика по версиям API
        versions_count = defaultdict(int)
        for e in endpoints:
            version = StatsFormatter._extract_version(e.path)
            versions_count[version] += 1
        
        # Статистика по тегам
        tags_count = defaultdict(int)
        for e in endpoints:
            if e.tags:
                for tag in e.tags:
                    tags_count[tag] += 1
            else:
                tags_count['Без тега'] += 1
        
        # Статистика по deprecated
        deprecated_count = sum(1 for e in endpoints if e.operation.get('deprecated', False))
        deprecated_percent = (deprecated_count / total * 100) if total > 0 else 0
        
        return {
            'total': total,
            'unique_paths': unique_paths,
            'with_summary': with_summary,
            'summary_percent': summary_percent,
            'without_tags': without_tags,
            'without_tags_percent': without_tags_percent,
            'methods': dict(methods_count),
            'versions': dict(versions_count),
            'tags': dict(tags_count),
            'deprecated': deprecated_count,
            'deprecated_percent': deprecated_percent,
        }
    
    @staticmethod
    def _extract_version(path: str) -> str:
        """
        Извлекает версию API из пути.
        
        Args:
            path: Путь эндпоинта
            
        Returns:
            Версия API (например, 'v1', 'v2') или 'без версии'
        """
        # Ищем паттерн /api/v{number}/ или /v{number}/
        match = re.search(r'/api/(v\d+)/', path)
        if match:
            return match.group(1)
        
        match = re.search(r'/(v\d+)/', path)
        if match:
            return match.group(1)
        
        return 'без версии'
    
    @staticmethod
    def format(stats: Dict, max_bar_length: int = 50) -> str:
        """
        Форматирует статистику для вывода.
        
        Args:
            stats: Словарь со статистикой
            max_bar_length: Максимальная длина полосы визуализации
            
        Returns:
            Отформатированная строка статистики
        """
        lines = []
        lines.append("📊 Статистика API\n")
        
        # Общая информация
        lines.append("Общая информация:\n")
        lines.append(f"  Всего эндпоинтов: {stats['total']}")
        lines.append(f"  Уникальных путей: {stats['unique_paths']}")
        lines.append(f"  Эндпоинтов с summary: {stats['with_summary']} ({stats['summary_percent']:.1f}%)")
        lines.append(f"  Эндпоинтов без тегов: {stats['without_tags']} ({stats['without_tags_percent']:.1f}%)")
        
        if stats['deprecated'] > 0:
            lines.append(f"  Эндпоинтов deprecated: {stats['deprecated']} ({stats['deprecated_percent']:.1f}%)")
        
        # Распределение по HTTP методам
        if stats['methods']:
            lines.append("\nРаспределение по HTTP методам:\n")
            total = stats['total']
            sorted_methods = sorted(stats['methods'].items(), key=lambda x: x[1], reverse=True)
            
            for method, count in sorted_methods:
                percent = (count / total * 100) if total > 0 else 0
                bar_length = int((count / total) * max_bar_length) if total > 0 else 0
                bar = '█' * bar_length
                lines.append(f"  {method:6} {count:3}  {bar}  {percent:5.1f}%")
        
        # Распределение по версиям API
        if stats['versions']:
            lines.append("\nРаспределение по версиям API:\n")
            total = stats['total']
            sorted_versions = sorted(stats['versions'].items(), key=lambda x: x[1], reverse=True)
            
            for version, count in sorted_versions:
                percent = (count / total * 100) if total > 0 else 0
                bar_length = int((count / total) * max_bar_length) if total > 0 else 0
                bar = '█' * bar_length
                lines.append(f"  {version:12} {count:3}  {bar}  {percent:5.1f}%")
        
        # Распределение по тегам
        if stats['tags']:
            lines.append("\nРаспределение по тегам:\n")
            total = stats['total']
            sorted_tags = sorted(stats['tags'].items(), key=lambda x: x[1], reverse=True)
            
            # Показываем топ-10 тегов, остальные сворачиваем
            max_tags_to_show = 10
            tags_to_show = sorted_tags[:max_tags_to_show]
            remaining_tags = sorted_tags[max_tags_to_show:]
            
            for tag, count in tags_to_show:
                percent = (count / total * 100) if total > 0 else 0
                lines.append(f"  {tag:20} {count:3}  ({percent:5.1f}%)")
            
            if remaining_tags:
                lines.append(f"  ... (еще {len(remaining_tags)} тегов)")
        
        return '\n'.join(lines)

