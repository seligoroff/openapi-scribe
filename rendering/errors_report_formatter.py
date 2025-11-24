"""Форматтер для отчета по кодам ошибок эндпоинтов"""
from typing import List, Dict


class ErrorsReportFormatter:
    """Форматтер для генерации отчета по кодам ошибок эндпоинтов"""
    
    @staticmethod
    def format(report_data: List[Dict[str, any]]) -> str:
        """
        Форматирует данные отчета в читаемый текст.
        
        Args:
            report_data: Список словарей с информацией об эндпоинтах:
                [
                    {
                        'path': '/api/users',
                        'method': 'GET',
                        'error_codes': ['400', '404', '500']
                    },
                    ...
                ]
        
        Returns:
            Отформатированная строка отчета
        """
        if not report_data:
            return "Эндпоинты не найдены."
        
        lines = []
        lines.append("Отчет по кодам ошибок эндпоинтов")
        lines.append("=" * 60)
        lines.append("")
        
        # Группируем по наличию ошибок
        endpoints_with_errors = []
        endpoints_without_errors = []
        
        for item in report_data:
            if item['error_codes']:
                endpoints_with_errors.append(item)
            else:
                endpoints_without_errors.append(item)
        
        # Выводим эндпоинты с ошибками
        if endpoints_with_errors:
            lines.append(f"Эндпоинты с кодами ошибок ({len(endpoints_with_errors)}):")
            lines.append("-" * 60)
            for item in endpoints_with_errors:
                error_codes_str = ", ".join(item['error_codes'])
                lines.append(f"{item['method']:6} {item['path']:40} [{error_codes_str}]")
            lines.append("")
        
        # Выводим эндпоинты без ошибок (если есть)
        if endpoints_without_errors:
            lines.append(f"Эндпоинты без кодов ошибок ({len(endpoints_without_errors)}):")
            lines.append("-" * 60)
            for item in endpoints_without_errors:
                lines.append(f"{item['method']:6} {item['path']}")
            lines.append("")
        
        # Итоговая статистика
        total_endpoints = len(report_data)
        total_error_codes = sum(len(item['error_codes']) for item in report_data)
        unique_error_codes = set()
        for item in report_data:
            unique_error_codes.update(item['error_codes'])
        
        lines.append("Статистика:")
        lines.append("-" * 60)
        lines.append(f"Всего эндпоинтов: {total_endpoints}")
        lines.append(f"Эндпоинтов с ошибками: {len(endpoints_with_errors)}")
        lines.append(f"Эндпоинтов без ошибок: {len(endpoints_without_errors)}")
        lines.append(f"Всего кодов ошибок: {total_error_codes}")
        lines.append(f"Уникальных кодов ошибок: {len(unique_error_codes)}")
        if unique_error_codes:
            lines.append(f"Коды: {', '.join(sorted(unique_error_codes))}")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_csv(report_data: List[Dict[str, any]]) -> str:
        """
        Форматирует данные отчета в CSV формат.
        
        Args:
            report_data: Список словарей с информацией об эндпоинтах
        
        Returns:
            CSV строка отчета
        """
        if not report_data:
            return "method,path,error_codes"
        
        lines = ["method,path,error_codes"]
        for item in report_data:
            error_codes_str = ";".join(item['error_codes']) if item['error_codes'] else ""
            lines.append(f"{item['method']},{item['path']},{error_codes_str}")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_markdown(report_data: List[Dict[str, any]]) -> str:
        """
        Форматирует данные отчета в Markdown формат.
        
        Args:
            report_data: Список словарей с информацией об эндпоинтах
        
        Returns:
            Markdown строка отчета
        """
        if not report_data:
            return "# Отчет по кодам ошибок эндпоинтов\n\nЭндпоинты не найдены."
        
        lines = []
        lines.append("# Отчет по кодам ошибок эндпоинтов")
        lines.append("")
        
        # Группируем по наличию ошибок
        endpoints_with_errors = []
        endpoints_without_errors = []
        
        for item in report_data:
            if item['error_codes']:
                endpoints_with_errors.append(item)
            else:
                endpoints_without_errors.append(item)
        
        # Выводим эндпоинты с ошибками
        if endpoints_with_errors:
            lines.append(f"## Эндпоинты с кодами ошибок ({len(endpoints_with_errors)})")
            lines.append("")
            lines.append("| Метод | Путь | Коды ошибок |")
            lines.append("|-------|------|-------------|")
            for item in endpoints_with_errors:
                error_codes_str = ", ".join(item['error_codes'])
                lines.append(f"| {item['method']} | `{item['path']}` | {error_codes_str} |")
            lines.append("")
        
        # Выводим эндпоинты без ошибок (если есть)
        if endpoints_without_errors:
            lines.append(f"## Эндпоинты без кодов ошибок ({len(endpoints_without_errors)})")
            lines.append("")
            lines.append("| Метод | Путь |")
            lines.append("|-------|------|")
            for item in endpoints_without_errors:
                lines.append(f"| {item['method']} | `{item['path']}` |")
            lines.append("")
        
        # Итоговая статистика
        total_endpoints = len(report_data)
        total_error_codes = sum(len(item['error_codes']) for item in report_data)
        unique_error_codes = set()
        for item in report_data:
            unique_error_codes.update(item['error_codes'])
        
        lines.append("## Статистика")
        lines.append("")
        lines.append(f"- **Всего эндпоинтов:** {total_endpoints}")
        lines.append(f"- **Эндпоинтов с ошибками:** {len(endpoints_with_errors)}")
        lines.append(f"- **Эндпоинтов без ошибок:** {len(endpoints_without_errors)}")
        lines.append(f"- **Всего кодов ошибок:** {total_error_codes}")
        lines.append(f"- **Уникальных кодов ошибок:** {len(unique_error_codes)}")
        if unique_error_codes:
            codes_list = ", ".join(sorted(unique_error_codes))
            lines.append(f"- **Коды:** {codes_list}")
        
        return "\n".join(lines)

