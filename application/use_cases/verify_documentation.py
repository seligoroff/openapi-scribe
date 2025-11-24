"""Use case для проверки информационных потерь в документации"""
from typing import List, Dict, Optional
from ports.spec_loader import SpecLoader
from domain.models import Endpoint
from domain.services import EndpointFinder
from rendering.verifier import DocumentationVerifier


class VerifyDocumentationUseCase:
    """
    Use case для проверки полноты информации в сгенерированной Markdown документации.
    
    Сравнивает данные из OpenAPI спецификации с Markdown и находит информационные потери.
    """
    
    def __init__(self, spec_loader: SpecLoader):
        """
        Инициализирует use case.
        
        Args:
            spec_loader: Адаптер для загрузки спецификаций
        """
        self.spec_loader = spec_loader
        self.finder = EndpointFinder()
        self.verifier = DocumentationVerifier()
    
    def verify_endpoint(
        self,
        spec_source: str,
        path: str,
        method: str,
        markdown_file: str
    ) -> Dict:
        """
        Проверяет полноту информации об эндпоинте в Markdown.
        
        Args:
            spec_source: Путь к файлу спецификации
            path: Путь эндпоинта
            method: HTTP метод
            markdown_file: Путь к файлу с Markdown документацией
            
        Returns:
            Словарь с результатами проверки
        """
        # Загрузка спецификации
        spec = self.spec_loader.load(spec_source)
        
        # Поиск эндпоинта
        endpoint = self.finder.find(spec, path, method)
        if not endpoint:
            raise ValueError(f"Эндпоинт {method} {path} не найден в спецификации")
        
        # Чтение Markdown файла
        try:
            with open(markdown_file, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Файл Markdown не найден: {markdown_file}")
        
        # Проверка
        return self.verifier.verify_endpoint(endpoint, markdown_content)
    
    def verify_all_endpoints(
        self,
        spec_source: str,
        markdown_file: str,
        endpoints_filter: Optional[List[tuple]] = None
    ) -> Dict:
        """
        Проверяет полноту информации для всех эндпоинтов в Markdown.
        
        Args:
            spec_source: Путь к файлу спецификации
            markdown_file: Путь к файлу с Markdown документацией
            endpoints_filter: Список кортежей (method, path) для фильтрации (опционально)
            
        Returns:
            Словарь с результатами проверки всех эндпоинтов
        """
        # Загрузка спецификации
        spec = self.spec_loader.load(spec_source)
        
        # Получение списка эндпоинтов
        endpoints = self.finder.list_all(spec)
        
        # Фильтрация (если указана)
        if endpoints_filter:
            filter_set = {(m.upper(), p) for m, p in endpoints_filter}
            endpoints = [
                e for e in endpoints
                if (e.method.upper(), e.path) in filter_set
            ]
        
        # Чтение Markdown файла
        try:
            with open(markdown_file, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Файл Markdown не найден: {markdown_file}")
        
        # Проверка каждого эндпоинта
        results = []
        total_issues = 0
        
        for endpoint in endpoints:
            result = self.verifier.verify_endpoint(endpoint, markdown_content)
            results.append(result)
            total_issues += result['issues_count']
        
        return {
            'total_endpoints': len(endpoints),
            'endpoints_with_issues': sum(1 for r in results if r['has_issues']),
            'total_issues': total_issues,
            'results': results
        }

