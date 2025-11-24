"""CLI интерфейс для OpenAPI Scribe"""
import sys
import os
import json
import click
from io import BytesIO
from adapters.input.file_spec_loader import FileSpecLoader
from application.use_cases import (
    GetEndpointInfoUseCase,
    GetSchemaInfoUseCase,
    ListEndpointsUseCase,
    GenerateDocumentationUseCase,
    VerifyDocumentationUseCase
)
from domain.services import SchemaResolver
from rendering.formatters import StatsFormatter

# Инициализация зависимостей
_spec_loader = FileSpecLoader()
_endpoint_use_case = GetEndpointInfoUseCase(_spec_loader)
_schema_use_case = GetSchemaInfoUseCase(_spec_loader)
_list_use_case = ListEndpointsUseCase(_spec_loader)
_generate_use_case = GenerateDocumentationUseCase(_spec_loader)
_verify_use_case = VerifyDocumentationUseCase(_spec_loader)


@click.group()
def cli():
    """Утилита для работы с OpenAPI спецификациями"""
    pass


# ============================================================================
# OpenAPI команды
# ============================================================================

@cli.command(name='endpoint')
@click.option('--spec', '-s', required=True, help='Путь к файлу openapi.json')
@click.option('--path', '-p', required=True, help='Путь эндпоинта API')
@click.option('--method', '-m', default='get', help='HTTP метод')
@click.option('--expand-schemas', is_flag=True, help='Рекурсивно выводить связанные схемы')
def find_endpoint_info(spec, path, method, expand_schemas):
    """Находит информацию об эндпоинте в OpenAPI спецификации"""
    try:
        # Использование use case для поиска эндпоинта
        endpoint = _endpoint_use_case.execute(spec, path, method)
        
        # Форматированный вывод
        click.echo(f"\nИнформация для {endpoint.method} {endpoint.path}:")
        click.echo(json.dumps(endpoint.operation, indent=2, ensure_ascii=False))

        # Рекурсивный вывод схем
        if expand_schemas:
            # Загружаем спецификацию для SchemaResolver
            spec_obj = _spec_loader.load(spec)
            resolver = SchemaResolver(spec_obj)
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
                                resolved_schema = resolver.resolve(ref)
                                if resolved_schema:
                                    click.echo(f"\n### Схема: {schema_name}")
                                    click.echo(json.dumps(resolved_schema, indent=2, ensure_ascii=False))
                                    # Рекурсивный обход свойств схемы
                                    find_and_print_schemas(resolved_schema)
                    
                    # Рекурсивный обход вложенных элементов
                    for key, value in node.items():
                        find_and_print_schemas(value)
                
                elif isinstance(node, list):
                    for item in node:
                        find_and_print_schemas(item)
            
            click.echo("\n\n### 🔍 Связанные схемы:")
            # Поиск схем в параметрах
            for param in endpoint.operation.get('parameters', []):
                find_and_print_schemas(param)
            
            # Поиск схем в теле запроса
            if 'requestBody' in endpoint.operation:
                find_and_print_schemas(endpoint.operation['requestBody'])
            
            # Поиск схем в ответах
            for response in endpoint.operation.get('responses', {}).values():
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
        # Использование use case для поиска схемы
        schema = _schema_use_case.execute(spec, name)
        
        if not schema:
            # Формируем список доступных схем для сообщения об ошибке
            spec_obj = _spec_loader.load(spec)
            available_schemas = list(spec_obj.schemas.keys())
            raise ValueError(
                f"Схема '{name}' не найдена. Доступные схемы: {', '.join(available_schemas)}"
            )
            
        # Форматированный вывод
        click.echo(f"\nСхема '{schema.name}':")
        click.echo(json.dumps(schema.definition, indent=2, ensure_ascii=False))
        
    except Exception as e:
        click.echo(f"Ошибка: {str(e)}", err=True)
        sys.exit(1)


@cli.command(name='list')
@click.option('--spec', '-s', required=True, help='Путь к файлу openapi.json')
@click.option('--output', '-o', help='Путь для сохранения отчёта (опционально)')
@click.option('--summary', is_flag=True, help='Показать краткое описание (summary) для каждого эндпоинта')
@click.option('--group-by-tags', is_flag=True, help='Группировать эндпоинты по тегам')
@click.option('--stats', is_flag=True, help='Показать статистику по API')
def list_endpoints(spec, output, summary, group_by_tags, stats):
    """
    Выводит список всех эндпоинтов API с методами.
    
    Поддерживает опции:
    - --summary: показывает краткое описание каждого эндпоинта
    - --group-by-tags: группирует эндпоинты по тегам (эндпоинты без тегов попадают в группу "Без тега")
    - --stats: показывает статистику по API (можно комбинировать с другими опциями)
    
    Опции можно комбинировать. Результат можно сохранить в файл с помощью --output.
    """
    try:
        # Использование use case для получения списка эндпоинтов
        endpoints_list = _list_use_case.execute(spec)
        
        # Вычисление и вывод статистики (если запрошена)
        stats_text = ""
        if stats:
            stats_data = StatsFormatter.calculate_stats(endpoints_list)
            stats_text = StatsFormatter.format(stats_data)
        
        # Если указан только --stats, выводим только статистику
        if stats and not summary and not group_by_tags:
            if output:
                expanded_output = os.path.expanduser(output)
                with open(expanded_output, 'w', encoding='utf-8') as f:
                    f.write(stats_text)
                click.echo(f"Статистика сохранена в: {expanded_output}")
            else:
                click.echo(stats_text)
            return
        
        # Группировка по тегам (если опция включена)
        if group_by_tags:
            from collections import defaultdict
            tags_dict = defaultdict(list)
            
            # Группируем эндпоинты по тегам
            for e in endpoints_list:
                # Форматирование эндпоинта с учетом опции summary
                endpoint_str = f"{e.method} {e.path}"
                if summary:
                    endpoint_summary = e.operation.get('summary', '')
                    if endpoint_summary:
                        endpoint_str += f" - {endpoint_summary}"
                
                # Добавляем эндпоинт в каждую группу тегов
                # Если у эндпоинта несколько тегов, он появится в каждой группе
                if e.tags:
                    for tag in e.tags:
                        tags_dict[tag].append(endpoint_str)
                else:
                    # Если тегов нет, добавляем в группу "Без тега"
                    tags_dict['Без тега'].append(endpoint_str)
            
            # Формируем вывод с группировкой
            # Сортировка тегов и эндпоинтов внутри групп для читаемости
            sorted_tags = sorted(tags_dict.keys())
            output_lines = []
            
            for tag in sorted_tags:
                output_lines.append(f"\n## {tag}")
                endpoints_in_tag = sorted(tags_dict[tag])
                output_lines.extend(endpoints_in_tag)
            
            result_text = '\n'.join(output_lines)
            
        else:
            # Обычный список без группировки
            if summary:
                # Форматирование с summary
                endpoints = []
                for e in endpoints_list:
                    endpoint_str = f"{e.method} {e.path}"
                    endpoint_summary = e.operation.get('summary', '')
                    if endpoint_summary:
                        endpoint_str += f" - {endpoint_summary}"
                    endpoints.append(endpoint_str)
            else:
                # Простое форматирование без summary
                endpoints = [f"{e.method} {e.path}" for e in endpoints_list]
            
            # Сортировка для удобства чтения
            endpoints.sort()
            result_text = '\n'.join(endpoints)

        # Сохранение или вывод результата
        if output:
            expanded_output = os.path.expanduser(output)
            # Если есть статистика, добавляем её в начало файла
            content = stats_text + "\n\n" + result_text if stats_text else result_text
            with open(expanded_output, 'w', encoding='utf-8') as f:
                f.write(content)
            click.echo(f"Отчёт сохранён в: {expanded_output}")
        else:
            # Вывод в консоль
            # Сначала статистика (если есть)
            if stats_text:
                click.echo(stats_text)
                click.echo()  # Пустая строка между статистикой и списком
            
            # Затем список (заголовок только для обычного списка)
            if not group_by_tags:
                click.echo("\nСписок эндпоинтов:")
            click.echo(result_text)
            
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
        # Использование use case для генерации документации
        markdown = _generate_use_case.execute(
            spec_source=spec,
            endpoints_filter=endpoints,
            include_all_schemas=all_schemas
        )
        
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


@cli.command(name='verify')
@click.option('--spec', '-s', required=True, help='Путь к файлу openapi.json')
@click.option('--markdown', '-m', required=True, help='Путь к файлу с Markdown документацией')
@click.option('--path', '-p', help='Путь эндпоинта для проверки (опционально, если не указан - проверяются все)')
@click.option('--method', help='HTTP метод (требуется вместе с --path)')
@click.option('--output', '-o', help='Путь для сохранения отчёта (опционально)')
def verify_documentation(spec, markdown, path, method, output):
    """
    Проверяет полноту информации в сгенерированной Markdown документации.
    
    Сравнивает данные из OpenAPI спецификации с Markdown и находит информационные потери:
    - Отсутствующие security требования
    - Потерянные примеры в responses, parameters, requestBody
    - Отсутствующий deprecated статус
    - Отсутствующий operationId или description
    """
    try:
        expanded_markdown = os.path.expanduser(markdown)
        
        if path and method:
            # Проверка одного эндпоинта
            result = _verify_use_case.verify_endpoint(
                spec_source=spec,
                path=path,
                method=method,
                markdown_file=expanded_markdown
            )
            
            # Форматированный вывод
            click.echo(f"\n🔍 Проверка эндпоинта: {result['endpoint']}")
            click.echo(f"\n{result['summary']}\n")
            
            if result['has_issues']:
                click.echo("Найденные проблемы:\n")
                for issue in result['issues']:
                    severity_icon = {
                        'high': '🔴',
                        'medium': '🟡',
                        'low': '🟢'
                    }.get(issue['severity'], '⚪')
                    click.echo(f"  {severity_icon} [{issue['severity'].upper()}] {issue['message']}")
                
                # Детали по потерянным элементам
                missing = result['missing_items']
                if missing['security']:
                    click.echo(f"\n  Отсутствует security: {json.dumps(missing['security'], ensure_ascii=False)}")
                if missing['deprecated']:
                    click.echo(f"\n  Отсутствует deprecated статус")
                if missing['operation_id']:
                    click.echo(f"\n  Отсутствует operationId")
                if missing['description']:
                    click.echo(f"\n  Отсутствует расширенное описание")
                if missing['response_examples']:
                    click.echo(f"\n  Отсутствуют примеры ответов: {len(missing['response_examples'])}")
                    for ex in missing['response_examples'][:5]:  # Показываем первые 5
                        click.echo(f"    - {ex['code']}: {ex['name']}")
                if missing['parameter_examples']:
                    click.echo(f"\n  Отсутствуют примеры параметров: {len(missing['parameter_examples'])}")
                if missing['request_body_examples']:
                    click.echo(f"\n  Отсутствуют примеры тела запроса: {len(missing['request_body_examples'])}")
            else:
                click.echo("✅ Все проверки пройдены успешно!")
            
            # Сохранение отчёта
            if output:
                expanded_output = os.path.expanduser(output)
                with open(expanded_output, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                click.echo(f"\n📄 Отчёт сохранён в: {expanded_output}")
        else:
            # Проверка всех эндпоинтов
            result = _verify_use_case.verify_all_endpoints(
                spec_source=spec,
                markdown_file=expanded_markdown
            )
            
            # Форматированный вывод
            click.echo(f"\n🔍 Проверка документации")
            click.echo(f"\nВсего эндпоинтов: {result['total_endpoints']}")
            click.echo(f"Эндпоинтов с проблемами: {result['endpoints_with_issues']}")
            click.echo(f"Всего проблем: {result['total_issues']}\n")
            
            if result['total_issues'] > 0:
                click.echo("Эндпоинты с проблемами:\n")
                for endpoint_result in result['results']:
                    if endpoint_result['has_issues']:
                        click.echo(f"  {endpoint_result['endpoint']}: {endpoint_result['issues_count']} проблем")
                        for issue in endpoint_result['issues'][:3]:  # Показываем первые 3 проблемы
                            severity_icon = {
                                'high': '🔴',
                                'medium': '🟡',
                                'low': '🟢'
                            }.get(issue['severity'], '⚪')
                            click.echo(f"    {severity_icon} {issue['message']}")
                        if endpoint_result['issues_count'] > 3:
                            click.echo(f"    ... и ещё {endpoint_result['issues_count'] - 3} проблем")
                        click.echo()
            else:
                click.echo("✅ Все проверки пройдены успешно!")
            
            # Сохранение отчёта
            if output:
                expanded_output = os.path.expanduser(output)
                with open(expanded_output, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                click.echo(f"\n📄 Отчёт сохранён в: {expanded_output}")
            
    except Exception as e:
        click.echo(f"Ошибка: {str(e)}", err=True)
        sys.exit(1)


# ============================================================================
# Markdown конвертация команды
# ============================================================================

def convert_with_mammoth(md_content, output_path):
    """Конвертация через Mammoth (чистый Python)"""
    try:
        import mammoth
    except ImportError:
        raise RuntimeError("Mammoth не установлен. Установите: pip install mammoth")

    # Поддержка разных версий Mammoth
    if hasattr(mammoth, 'convert_to_docx'):
        # Старая версия (<1.6.0)
        result = mammoth.convert_to_docx(md_content)
        docx_bytes = result.value
    else:
        # Новая версия (1.6.0+)
        # Создаем байтовый поток из содержимого
        file_obj = BytesIO(md_content.encode('utf-8'))
        result = mammoth.convert(file_obj)
        docx_bytes = result.value

    with open(output_path, "wb") as f:
        f.write(docx_bytes)
    
    if result.messages:
        click.secho("\nПредупреждения Mammoth:", fg='yellow')
        for message in result.messages:
            click.echo(f"- {message.message}")


def convert_with_pandoc(md_content, output_path):
    """Конвертация через Pandoc (требует установки pandoc)"""
    try:
        import pypandoc
    except ImportError:
        raise RuntimeError("pypandoc не установлен. Установите: pip install pypandoc")

    # Определяем формат по расширению файла
    output_ext = os.path.splitext(output_path)[1].lstrip(".").lower()
    actual_output_path = output_path
    
    # Поддержка .doc через RTF-конвертацию
    if output_ext == "doc":
        # Временно меняем расширение на .rtf для конвертации
        actual_output_path = os.path.splitext(output_path)[0] + ".rtf"
        output_ext = "rtf"
        click.secho("Внимание: Pandoc не поддерживает прямой вывод в .doc. Используем RTF-формат.", fg='yellow')
    
    # Конвертируем с поддержкой таблиц
    # Используем gfm (GitHub Flavored Markdown) для лучшей поддержки таблиц
    extra_args = [
        "--standalone",
        "--wrap=none",  # Не переносить строки в таблицах
    ]
    
    # Для RTF и DOC добавляем дополнительные параметры для таблиц
    if output_ext in ("rtf", "doc"):
        extra_args.extend([
            "--columns=10000",  # Широкие таблицы
        ])
    
    pypandoc.convert_text(
        md_content,
        output_ext,
        format="gfm",  # GitHub Flavored Markdown для лучшей поддержки таблиц
        outputfile=actual_output_path,
        extra_args=extra_args
    )
    
    return actual_output_path


@cli.command(name='md2doc')
@click.argument('input', type=click.Path(exists=True, dir_okay=False))
@click.argument('output', type=click.Path())
@click.option('--engine', 
              type=click.Choice(['auto', 'mammoth', 'pandoc'], case_sensitive=False),
              default='auto',
              show_default=True,
              help="""Движок конвертации:
  auto   = Mammoth для DOCX, Pandoc для DOC
  mammoth = Чистый Python (только DOCX)
  pandoc  = Требует установки Pandoc (поддержка DOC/DOCX)""")
def md2doc_command(input, output, engine):
    """
    Конвертер Markdown в DOC/DOCX
    
    Примеры:
    
    \b
      python cli.py md2doc input.md output.docx
      python cli.py md2doc input.md output.doc --engine=pandoc
    """
    
    # Проверка расширений файлов
    if not input.lower().endswith(".md"):
        click.secho("Ошибка: входной файл должен иметь расширение .md", fg='red')
        sys.exit(1)
    
    if not output.lower().endswith((".docx", ".doc", ".rtf")):
        click.secho("Ошибка: выходной файл должен быть .docx, .doc или .rtf", fg='red')
        sys.exit(1)

    # Чтение исходного файла
    try:
        with open(input, "r", encoding="utf-8") as f:
            md_content = f.read()
        click.secho(f"✓ Файл прочитан: {input}", fg='green')
    except Exception as e:
        click.secho(f"Ошибка чтения файла: {e}", fg='red')
        sys.exit(1)

    # Выбор движка
    output_ext = os.path.splitext(output)[1].lower()
    
    if engine == "auto":
        engine = "pandoc" if output_ext == ".doc" else "mammoth"
        click.secho(f"Автовыбор движка: {engine}", fg='blue')

    # Конвертация
    try:
        if engine == "mammoth":
            if output_ext == ".doc":
                click.secho("Ошибка: Mammoth поддерживает только DOCX", fg='red')
                sys.exit(1)
                
            convert_with_mammoth(md_content, output)
            click.secho(f"✓ Успешно! Конвертировано через Mammoth -> {output}", fg='green')
        
        elif engine == "pandoc":
            actual_output = convert_with_pandoc(md_content, output)
            
            # Если указан .doc, но создан .rtf файл, переименовываем обратно в .doc
            if output_ext == ".doc" and actual_output != output:
                if os.path.exists(actual_output):
                    os.rename(actual_output, output)
                    click.secho(f"✓ Успешно! Конвертировано через Pandoc -> {output}", fg='green')
                else:
                    click.secho(f"✓ Успешно! Конвертировано через Pandoc -> {actual_output}", fg='green')
            else:
                click.secho(f"✓ Успешно! Конвертировано через Pandoc -> {output}", fg='green')
    
    except Exception as e:
        click.secho(f"\nОшибка конвертации ({engine}): {e}", fg='red')
        if "pandoc" in str(e).lower():
            click.secho("\nУбедитесь что установлен Pandoc: https://pandoc.org/installing.html", fg='yellow')
        sys.exit(1)


if __name__ == "__main__":
    cli()

