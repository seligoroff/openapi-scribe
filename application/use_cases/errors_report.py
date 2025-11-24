"""Use case для генерации отчета по эндпоинтам с кодами ошибок"""
from typing import List, Dict, Set
from ports.spec_loader import SpecLoader
from domain.models import Endpoint
from domain.services import EndpointFinder
from rendering.errors_report_formatter import ErrorsReportFormatter


class ErrorsReportUseCase:
    """
    Use case для генерации отчета по эндпоинтам с кодами ошибок.
    
    Извлекает из каждого эндпоинта путь, метод и коды ошибок (4xx, 5xx) из responses.
    """
    
    def __init__(self, spec_loader: SpecLoader):
        """
        Инициализирует use case.
        
        Args:
            spec_loader: Адаптер для загрузки спецификаций
        """
        self.spec_loader = spec_loader
        self.finder = EndpointFinder()
    
    def execute(self, spec_source: str) -> List[Dict[str, any]]:
        """
        Генерирует отчет по эндпоинтам с кодами ошибок.
        
        Args:
            spec_source: Путь к файлу спецификации
            
        Returns:
            Список словарей с информацией об эндпоинтах:
            [
                {
                    'path': '/api/users',
                    'method': 'GET',
                    'error_codes': ['400', '404', '500']
                },
                ...
            ]
            
        Raises:
            FileNotFoundError: Если файл спецификации не найден
            IOError: Если произошла ошибка при чтении файла
        """
        # Загрузка спецификации
        spec = self.spec_loader.load(spec_source)
        
        # Получение списка эндпоинтов
        endpoints = self.finder.list_all(spec)
        
        # Извлечение информации об ошибках для каждого эндпоинта
        report_data = []
        for endpoint in endpoints:
            error_codes = self._extract_error_codes(endpoint)
            report_data.append({
                'path': endpoint.path,
                'method': endpoint.method,
                'error_codes': sorted(error_codes) if error_codes else []
            })
        
        return report_data
    
    def format_report(self, report_data: List[Dict[str, any]], format_type: str = 'text') -> str:
        """
        Форматирует отчет в указанном формате.
        
        Args:
            report_data: Данные отчета
            format_type: Тип формата ('text', 'csv' или 'md')
            
        Returns:
            Отформатированная строка отчета
        """
        if format_type == 'csv':
            return ErrorsReportFormatter.format_csv(report_data)
        elif format_type == 'md':
            return ErrorsReportFormatter.format_markdown(report_data)
        return ErrorsReportFormatter.format(report_data)
    
    def _extract_error_codes(self, endpoint: Endpoint) -> Set[str]:
        """
        Извлекает коды ошибок (4xx, 5xx) из responses эндпоинта.
        
        Args:
            endpoint: Эндпоинт для анализа
            
        Returns:
            Множество кодов ошибок
        """
        error_codes = set()
        responses = endpoint.operation.get('responses', {})
        
        for code_str in responses.keys():
            # Пропускаем диапазоны типа "default" или "2XX"
            if not code_str.isdigit():
                # Проверяем диапазоны типа "4XX", "5XX"
                if code_str.upper() in ('4XX', '5XX'):
                    error_codes.add(code_str.upper())
                continue
            
            code = int(code_str)
            # Извлекаем только коды ошибок (4xx и 5xx)
            if 400 <= code < 600:
                error_codes.add(code_str)
        
        return error_codes

