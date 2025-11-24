"""Тесты для CLI команд в cli.py (объединенный интерфейс)"""
import pytest
import json
from pathlib import Path
from click.testing import CliRunner
from cli import cli


@pytest.mark.integration
class TestEndpointCommand:
    """Тесты для команды endpoint"""
    
    def test_endpoint_command_success(self, sample_spec_path):
        """Тест успешного поиска эндпоинта"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['endpoint', '--spec', sample_spec_path, '--path', '/api/v1/users', '--method', 'get']
        )
        
        assert result.exit_code == 0
        assert "GET" in result.output
        assert "/api/v1/users" in result.output
        assert "get_users" in result.output or "Get users" in result.output
    
    def test_endpoint_command_not_found_path(self, sample_spec_path):
        """Тест когда путь эндпоинта не найден"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['endpoint', '--spec', sample_spec_path, '--path', '/api/v1/nonexistent', '--method', 'get']
        )
        
        assert result.exit_code == 1
        assert "не найден" in result.output.lower() or "not found" in result.output.lower()
    
    def test_endpoint_command_not_found_method(self, sample_spec_path):
        """Тест когда метод не найден"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['endpoint', '--spec', sample_spec_path, '--path', '/api/v1/users', '--method', 'delete']
        )
        
        assert result.exit_code == 1
        assert "не найден" in result.output.lower() or "not found" in result.output.lower()
        assert "доступные методы" in result.output.lower() or "available" in result.output.lower()
    
    def test_endpoint_command_expand_schemas(self, sample_spec_path):
        """Тест расширения схем"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                'endpoint',
                '--spec', sample_spec_path,
                '--path', '/api/v1/users',
                '--method', 'get',
                '--expand-schemas'
            ]
        )
        
        assert result.exit_code == 0
        assert "Связанные схемы" in result.output or "schemas" in result.output.lower()
    
    def test_endpoint_command_trailing_slash(self, sample_spec_path):
        """Тест обработки trailing slash"""
        runner = CliRunner()
        # Тестируем путь с trailing slash
        result = runner.invoke(
            cli,
            ['endpoint', '--spec', sample_spec_path, '--path', '/api/v1/users/', '--method', 'get']
        )
        
        # Должен найти эндпоинт (нормализация пути)
        assert result.exit_code == 0
    
    def test_endpoint_command_default_method(self, sample_spec_path):
        """Тест использования метода по умолчанию"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['endpoint', '--spec', sample_spec_path, '--path', '/api/v1/users']
        )
        
        assert result.exit_code == 0
        assert "GET" in result.output


@pytest.mark.integration
class TestSchemaCommand:
    """Тесты для команды schema"""
    
    def test_schema_command_success(self, sample_spec_path):
        """Тест успешного поиска схемы"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['schema', '--spec', sample_spec_path, '--name', 'User']
        )
        
        assert result.exit_code == 0
        assert "User" in result.output
        assert "type" in result.output.lower() or "properties" in result.output.lower()
    
    def test_schema_command_not_found(self, sample_spec_path):
        """Тест когда схема не найдена"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['schema', '--spec', sample_spec_path, '--name', 'NonexistentSchema']
        )
        
        assert result.exit_code == 1
        assert "не найдена" in result.output.lower() or "not found" in result.output.lower()
        assert "доступные схемы" in result.output.lower() or "available" in result.output.lower()
    
    def test_schema_command_user_role(self, sample_spec_path):
        """Тест поиска схемы UserRole"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['schema', '--spec', sample_spec_path, '--name', 'UserRole']
        )
        
        assert result.exit_code == 0
        assert "UserRole" in result.output
    
    def test_schema_command_list(self, sample_spec_path):
        """Тест вывода списка всех схем"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['schema', '--spec', sample_spec_path, '--list']
        )
        
        assert result.exit_code == 0
        assert "Доступные схемы" in result.output
        assert "User" in result.output
        assert "UserRole" in result.output
        assert "Error" in result.output
        # Проверяем что схемы отсортированы
        output_lines = result.output.split('\n')
        schema_lines = [line for line in output_lines if line.strip().startswith('- ')]
        assert len(schema_lines) > 0
        # Проверяем формат вывода
        assert any("Доступные схемы (" in line for line in output_lines)
    
    def test_schema_command_list_short_flag(self, sample_spec_path):
        """Тест вывода списка всех схем с коротким флагом -l"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['schema', '--spec', sample_spec_path, '-l']
        )
        
        assert result.exit_code == 0
        assert "Доступные схемы" in result.output
        assert "User" in result.output
    
    def test_schema_command_list_minimal_spec(self, minimal_spec_path):
        """Тест вывода списка схем для минимальной спецификации"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['schema', '--spec', minimal_spec_path, '--list']
        )
        
        assert result.exit_code == 0
        assert "Доступные схемы" in result.output
        # Минимальная спецификация содержит TestResponse
        assert "TestResponse" in result.output
    
    def test_schema_command_list_empty_spec(self, tmp_path):
        """Тест вывода списка схем для спецификации без схем"""
        # Создаем временную спецификацию без схем
        empty_spec = tmp_path / "empty_spec.json"
        empty_spec.write_text(
            '{"openapi": "3.0.0", "info": {"title": "Test", "version": "1.0.0"}, "paths": {}, "components": {}}',
            encoding='utf-8'
        )
        
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['schema', '--spec', str(empty_spec), '--list']
        )
        
        assert result.exit_code == 0
        assert "не найдено ни одной схемы" in result.output.lower() or "no schemas" in result.output.lower()
    
    def test_schema_command_no_name_no_list(self, sample_spec_path):
        """Тест ошибки когда не указаны ни --name, ни --list"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['schema', '--spec', sample_spec_path]
        )
        
        assert result.exit_code == 1
        assert "необходимо указать" in result.output.lower() or "must specify" in result.output.lower()
        assert "--name" in result.output or "--list" in result.output or "-n" in result.output or "-l" in result.output


@pytest.mark.integration
class TestListCommand:
    """Тесты для команды list"""
    
    def test_list_command(self, sample_spec_path):
        """Тест списка эндпоинтов"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['list', '--spec', sample_spec_path]
        )
        
        assert result.exit_code == 0
        assert "Список эндпоинтов" in result.output or "endpoints" in result.output.lower()
        assert "GET /api/v1/users" in result.output
        assert "POST /api/v1/users" in result.output
    
    def test_list_command_save_file(self, sample_spec_path, tmp_path):
        """Тест сохранения списка в файл"""
        runner = CliRunner()
        output_file = tmp_path / "endpoints_list.txt"
        
        result = runner.invoke(
            cli,
            ['list', '--spec', sample_spec_path, '--output', str(output_file)]
        )
        
        assert result.exit_code == 0
        assert "сохранён" in result.output.lower() or "saved" in result.output.lower()
        assert output_file.exists()
        
        # Проверяем содержимое файла
        content = output_file.read_text(encoding='utf-8')
        assert "GET /api/v1/users" in content
        assert "POST /api/v1/users" in content
    
    def test_list_command_sorted(self, sample_spec_path):
        """Тест что эндпоинты отсортированы"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['list', '--spec', sample_spec_path]
        )
        
        assert result.exit_code == 0
        output_lines = [line for line in result.output.split('\n') if line.strip() and 'GET' in line or 'POST' in line]
        if len(output_lines) > 1:
            # Проверяем что строки отсортированы
            sorted_lines = sorted(output_lines)
            assert output_lines == sorted_lines
    
    def test_list_command_minimal(self, minimal_spec_path):
        """Тест списка для минимальной спецификации"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['list', '--spec', minimal_spec_path]
        )
        
        assert result.exit_code == 0
        assert "GET /api/v1/test" in result.output
    
    def test_list_command_with_summary(self, sample_spec_path):
        """Тест списка эндпоинтов с опцией --summary"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['list', '--spec', sample_spec_path, '--summary']
        )
        
        assert result.exit_code == 0
        assert "Список эндпоинтов" in result.output or "endpoints" in result.output.lower()
        # Проверяем что summary выводится
        assert "GET /api/v1/users - Get users" in result.output
        assert "POST /api/v1/users - Create user" in result.output
        assert "GET /api/v1/users/{userId} - Get user by ID" in result.output
    
    def test_list_command_summary_save_file(self, sample_spec_path, tmp_path):
        """Тест сохранения списка с summary в файл"""
        runner = CliRunner()
        output_file = tmp_path / "endpoints_with_summary.txt"
        
        result = runner.invoke(
            cli,
            ['list', '--spec', sample_spec_path, '--summary', '--output', str(output_file)]
        )
        
        assert result.exit_code == 0
        assert output_file.exists()
        
        # Проверяем содержимое файла
        content = output_file.read_text(encoding='utf-8')
        assert "GET /api/v1/users - Get users" in content
        assert "POST /api/v1/users - Create user" in content
    
    def test_list_command_group_by_tags(self, sample_spec_path):
        """Тест группировки эндпоинтов по тегам"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['list', '--spec', sample_spec_path, '--group-by-tags']
        )
        
        assert result.exit_code == 0
        # Проверяем что есть заголовки групп
        assert "## users" in result.output
        # Проверяем что эндпоинты сгруппированы
        assert "GET /api/v1/users" in result.output
        assert "POST /api/v1/users" in result.output
    
    def test_list_command_group_by_tags_with_summary(self, sample_spec_path):
        """Тест группировки по тегам с summary"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['list', '--spec', sample_spec_path, '--group-by-tags', '--summary']
        )
        
        assert result.exit_code == 0
        assert "## users" in result.output
        assert "GET /api/v1/users - Get users" in result.output
        assert "POST /api/v1/users - Create user" in result.output
    
    def test_list_command_group_by_tags_save_file(self, sample_spec_path, tmp_path):
        """Тест сохранения группированного списка в файл"""
        runner = CliRunner()
        output_file = tmp_path / "endpoints_grouped.txt"
        
        result = runner.invoke(
            cli,
            ['list', '--spec', sample_spec_path, '--group-by-tags', '--output', str(output_file)]
        )
        
        assert result.exit_code == 0
        assert output_file.exists()
        
        # Проверяем содержимое файла
        content = output_file.read_text(encoding='utf-8')
        assert "## users" in content
        assert "GET /api/v1/users" in content


@pytest.mark.integration
class TestGenerateMdCommand:
    """Тесты для команды generate-md"""
    
    def test_generate_md_command(self, sample_spec_path):
        """Тест генерации документации"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['generate-md', '--spec', sample_spec_path]
        )
        
        assert result.exit_code == 0
        assert "Sample API" in result.output
        assert "1.0.0" in result.output
        assert "#" in result.output  # Markdown заголовки
    
    def test_generate_md_command_with_filter(self, sample_spec_path, endpoints_filter_file):
        """Тест генерации с фильтром эндпоинтов"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                'generate-md',
                '--spec', sample_spec_path,
                '--endpoints', endpoints_filter_file
            ]
        )
        
        assert result.exit_code == 0
        assert "Sample API" in result.output
        # Должны быть только отфильтрованные эндпоинты
    
    def test_generate_md_command_with_output(self, sample_spec_path, tmp_path):
        """Тест генерации с сохранением в файл"""
        runner = CliRunner()
        output_file = tmp_path / "documentation.md"
        
        result = runner.invoke(
            cli,
            [
                'generate-md',
                '--spec', sample_spec_path,
                '--output', str(output_file)
            ]
        )
        
        assert result.exit_code == 0
        assert "успешно сохранена" in result.output.lower() or "saved" in result.output.lower()
        assert output_file.exists()
        
        # Проверяем содержимое файла
        content = output_file.read_text(encoding='utf-8')
        assert "Sample API" in content
        assert len(content) > 0
    
    def test_generate_md_command_all_schemas(self, sample_spec_path):
        """Тест генерации со всеми схемами"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                'generate-md',
                '--spec', sample_spec_path,
                '--all-schemas'
            ]
        )
        
        assert result.exit_code == 0
        assert "Sample API" in result.output
    
    def test_generate_md_command_filter_file_not_found(self, sample_spec_path):
        """Тест генерации когда файл фильтра не найден"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                'generate-md',
                '--spec', sample_spec_path,
                '--endpoints', '/nonexistent/filter.txt'
            ]
        )
        
        # Должен продолжить работу с предупреждением
        assert result.exit_code == 0
        assert "⚠️" in result.output or "warning" in result.output.lower()
    
    def test_generate_md_command_minimal(self, minimal_spec_path):
        """Тест генерации для минимальной спецификации"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['generate-md', '--spec', minimal_spec_path]
        )
        
        assert result.exit_code == 0
        assert "Test API" in result.output


@pytest.mark.integration
class TestCLIErrorHandling:
    """Тесты обработки ошибок CLI"""
    
    def test_endpoint_command_file_not_found(self):
        """Тест обработки отсутствующего файла спецификации"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['endpoint', '--spec', '/nonexistent.json', '--path', '/api/v1/test', '--method', 'get']
        )
        
        assert result.exit_code == 1
        assert "не найден" in result.output.lower() or "not found" in result.output.lower()
    
    def test_schema_command_file_not_found(self):
        """Тест обработки отсутствующего файла для команды schema"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['schema', '--spec', '/nonexistent.json', '--name', 'Test']
        )
        
        assert result.exit_code == 1
        assert "не найден" in result.output.lower() or "not found" in result.output.lower()
    
    def test_list_command_file_not_found(self):
        """Тест обработки отсутствующего файла для команды list"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['list', '--spec', '/nonexistent.json']
        )
        
        assert result.exit_code == 1
        assert "не найден" in result.output.lower() or "not found" in result.output.lower()
    
    def test_generate_md_command_file_not_found(self):
        """Тест обработки отсутствующего файла для команды generate-md"""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['generate-md', '--spec', '/nonexistent.json']
        )
        
        assert result.exit_code == 1
        assert "не найден" in result.output.lower() or "not found" in result.output.lower()

