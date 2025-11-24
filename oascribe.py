import sys
import os
import json
import click
from oatools import load_openapi_spec, load_endpoints_filter, generate_markdown

@click.group()
def cli():
    """Утилита для работы с OpenAPI спецификациями"""
    pass

@cli.command(name='endpoint')
@click.option('--spec', '-s', required=True, help='Путь к файлу openapi.json')
@click.option('--path', '-p', required=True, help='Путь эндпоинта API')
@click.option('--method', '-m', default='get', help='HTTP метод')
@click.option('--expand-schemas', is_flag=True, help='Рекурсивно выводить связанные схемы')
def find_endpoint_info(spec, path, method, expand_schemas):
    try:
        openapi_spec = load_openapi_spec(spec)

        # Нормализация URL (удаление trailing slash)
        endpoint_path = path.rstrip('/')
        
        # Поиск совпадения по URL
        paths = openapi_spec.get('paths', {})
        exact_match = paths.get(endpoint_path)
        
        if not exact_match:
            # Попытка найти вариант с trailing slash
            alt_path = endpoint_path + '/'
            exact_match = paths.get(alt_path)
            if exact_match:
                endpoint_path = alt_path

        if not exact_match:
            raise ValueError(f"Путь '{path}' не найден в спецификации")

        # Проверка метода
        method = method.lower()
        endpoint_info = exact_match.get(method)
        
        if not endpoint_info:
            available_methods = [m.upper() for m in exact_match.keys()]
            raise ValueError(
                f"Метод {method.upper()} не найден. Доступные методы: {', '.join(available_methods)}"
            )

        # Форматированный вывод
        click.echo(f"\nИнформация для {method.upper()} {endpoint_path}:")
        click.echo(json.dumps(endpoint_info, indent=2, ensure_ascii=False))

        # Рекурсивный вывод схем
        if expand_schemas:
            visited_schemas = set()
            
            def find_and_print_schemas(node):
                if isinstance(node, dict):
                    # Обработка ссылок
                    if '$ref' in node:
                        ref = node['$ref']
                        if ref.startswith('#/components/schemas/'):
                            schema_name = ref.split('/')[-1]
                            if schema_name not in visited_schemas:
                                visited_schemas.add(schema_name)
                                schema = openapi_spec['components']['schemas'].get(schema_name)
                                if schema:
                                    click.echo(f"\n### Схема: {schema_name}")
                                    click.echo(json.dumps(schema, indent=2, ensure_ascii=False))
                                    # Рекурсивный обход свойств схемы
                                    find_and_print_schemas(schema)
                    
                    # Рекурсивный обход вложенных элементов
                    for key, value in node.items():
                        find_and_print_schemas(value)
                
                elif isinstance(node, list):
                    for item in node:
                        find_and_print_schemas(item)
            
            click.echo("\n\n### 🔍 Связанные схемы:")
            # Поиск схем в параметрах
            for param in endpoint_info.get('parameters', []):
                find_and_print_schemas(param)
            
            # Поиск схем в теле запроса
            if 'requestBody' in endpoint_info:
                find_and_print_schemas(endpoint_info['requestBody'])
            
            # Поиск схем в ответах
            for response in endpoint_info.get('responses', {}).values():
                find_and_print_schemas(response)
            
            if not visited_schemas:
                click.echo("Связанные схемы не обнаружены")
        
    except Exception as e:
        click.echo(f"Ошибка: {str(e)}", err=True)
        sys.exit(1)

@cli.command(name='schema')
@click.option('--spec', '-s', required=True, help='Путь к файлу openapi.json')
@click.option('--name', '-n', required=True, help='Имя схемы для поиска')
def find_schema_info(spec, name):
    """Находит определение схемы в OpenAPI спецификации"""
    try:
        openapi_spec = load_openapi_spec(spec)
        
        # Получаем раздел 'components/schemas'
        schemas = openapi_spec.get('components', {}).get('schemas', {})
        
        # Ищем схему по имени
        schema_info = schemas.get(name)
        
        if not schema_info:
            # Формируем список доступных схем для сообщения об ошибке
            available_schemas = list(schemas.keys())
            raise ValueError(
                f"Схема '{name}' не найдена. Доступные схемы: {', '.join(available_schemas)}"
            )
            
        # Форматированный вывод
        click.echo(f"\nСхема '{name}':")
        click.echo(json.dumps(schema_info, indent=2, ensure_ascii=False))
        
    except Exception as e:
        click.echo(f"Ошибка: {str(e)}", err=True)
        sys.exit(1)
        

@cli.command(name='list')
@click.option('--spec', '-s', required=True, help='Путь к файлу openapi.json')
@click.option('--output', '-o', help='Путь для сохранения отчёта (опционально)')
def list_endpoints(spec, output):
    """Выводит список всех эндпоинтов API с методами"""
    try:
        openapi_spec = load_openapi_spec(spec)
        
        # Извлечение путей и методов
        endpoints = []
        for path, methods in openapi_spec.get('paths', {}).items():
            for method in methods.keys():
                # Фильтрация только стандартных HTTP методов
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
                    endpoints.append(f"{method.upper()} {path}")

        # Сортировка для удобства чтения
        endpoints.sort()

        # Сохранение или вывод
        if output:
            expanded_output = os.path.expanduser(output)
            with open(expanded_output, 'w', encoding='utf-8') as f:
                f.write('\n'.join(endpoints))
            click.echo(f"Отчёт сохранён в: {expanded_output}")
        else:
            click.echo("\nСписок эндпоинтов:")
            click.echo('\n'.join(endpoints))
            
    except Exception as e:
        click.echo(f"Ошибка: {str(e)}", err=True)
        sys.exit(1)

@cli.command(name='generate-md')
@click.option('--spec', '-s', required=True, help='Путь к файлу openapi.json')
@click.option('--endpoints', '-e', help='Файл со списком эндпоинтов для фильтрации (опционально)')
@click.option('--output', '-o', help='Файл для вывода документации (опционально)')
@click.option('--all-schemas', is_flag=True, help='Включить все схемы, а не только используемые')
def generate_markdown_command(spec, endpoints, output, all_schemas):
    """Генерирует Markdown документацию из OpenAPI спецификации"""
    try:
        # Загрузка OpenAPI спецификации
        openapi_spec = load_openapi_spec(spec)
        
        # Загрузка фильтра эндпоинтов
        endpoints_filter = None
        if endpoints:
            try:
                endpoints_filter = load_endpoints_filter(endpoints)
            except FileNotFoundError as e:
                click.echo(f"⚠️ {str(e)}. Будут обработаны все эндпоинты.", err=True)
        
        # Генерация документации
        markdown = generate_markdown(openapi_spec, endpoints_filter, include_all_schemas=all_schemas)
        
        # Вывод результата
        if output:
            expanded_output = os.path.expanduser(output)
            with open(expanded_output, 'w', encoding='utf-8') as f:
                f.write(markdown)
            click.echo(f"✅ Документация успешно сохранена в {expanded_output}")
        else:
            click.echo(markdown)
            
    except Exception as e:
        click.echo(f"Ошибка: {str(e)}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    cli()