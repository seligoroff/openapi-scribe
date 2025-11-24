"""Тесты для adapters/input/file_spec_loader.py"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
from adapters.input.file_spec_loader import FileSpecLoader
from domain.models import OpenAPISpec
from ports.spec_loader import SpecLoader


@pytest.mark.unit
class TestFileSpecLoader:
    """Тесты для FileSpecLoader"""
    
    def test_file_spec_loader_implements_interface(self):
        """Тест что FileSpecLoader реализует SpecLoader"""
        loader = FileSpecLoader()
        assert isinstance(loader, SpecLoader)
    
    def test_load_success(self, sample_spec_path):
        """Тест успешной загрузки спецификации"""
        loader = FileSpecLoader()
        spec = loader.load(sample_spec_path)
        
        assert isinstance(spec, OpenAPISpec)
        assert spec.info['title'] == "Sample API"
        assert len(spec.paths) > 0
    
    def test_load_file_not_found(self):
        """Тест обработки отсутствующего файла"""
        loader = FileSpecLoader()
        
        with pytest.raises(FileNotFoundError, match="не найден"):
            loader.load("/nonexistent/file.json")
    
    def test_load_invalid_json(self, tmp_path):
        """Тест обработки невалидного JSON"""
        loader = FileSpecLoader()
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid json }", encoding='utf-8')
        
        with pytest.raises(ValueError, match="Невалидный JSON"):
            loader.load(str(invalid_file))
    
    def test_load_tilde_expansion(self, tmp_path, monkeypatch):
        """Тест расширения пути с тильдой"""
        loader = FileSpecLoader()
        
        # Создаем временный файл
        test_file = tmp_path / "test.json"
        spec_dict = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {},
            "components": {"schemas": {}}
        }
        test_file.write_text(json.dumps(spec_dict), encoding='utf-8')
        
        # Мокаем expanduser для возврата нашего пути
        def mock_expanduser(path):
            if path.startswith('~'):
                return str(test_file)
            return path
        
        monkeypatch.setattr('os.path.expanduser', lambda p: mock_expanduser(p))
        
        spec = loader.load(f"~/{test_file.name}")
        assert isinstance(spec, OpenAPISpec)
    
    def test_load_io_error(self, tmp_path, monkeypatch):
        """Тест обработки ошибки чтения файла"""
        loader = FileSpecLoader()
        test_file = tmp_path / "test.json"
        test_file.write_text('{"test": "data"}', encoding='utf-8')
        
        # Мокаем open для выброса IOError
        def mock_open_error(*args, **kwargs):
            raise IOError("Permission denied")
        
        monkeypatch.setattr('builtins.open', mock_open_error)
        
        with pytest.raises(IOError, match="Ошибка чтения"):
            loader.load(str(test_file))
    
    def test_load_creates_openapi_spec(self, sample_spec_path):
        """Тест что load создает OpenAPISpec"""
        loader = FileSpecLoader()
        spec = loader.load(sample_spec_path)
        
        assert isinstance(spec, OpenAPISpec)
        assert spec.raw is not None
        assert spec.paths is not None
        assert spec.schemas is not None
        assert spec.info is not None
    
    def test_load_minimal_spec(self, minimal_spec_path):
        """Тест загрузки минимальной спецификации"""
        loader = FileSpecLoader()
        spec = loader.load(minimal_spec_path)
        
        assert isinstance(spec, OpenAPISpec)
        assert spec.info['title'] == "Test API"
    
    def test_load_preserves_all_data(self, sample_spec_path):
        """Тест что все данные сохраняются в raw"""
        loader = FileSpecLoader()
        spec = loader.load(sample_spec_path)
        
        # Проверяем что raw содержит все данные
        assert 'openapi' in spec.raw
        assert 'info' in spec.raw
        assert 'paths' in spec.raw
        assert 'components' in spec.raw
    
    def test_load_realpath_resolution(self, tmp_path):
        """Тест разрешения реального пути"""
        loader = FileSpecLoader()
        
        # Создаем файл
        test_file = tmp_path / "test.json"
        spec_dict = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {},
            "components": {"schemas": {}}
        }
        test_file.write_text(json.dumps(spec_dict), encoding='utf-8')
        
        spec = loader.load(str(test_file))
        assert isinstance(spec, OpenAPISpec)
    
    def test_load_utf8_encoding(self, tmp_path):
        """Тест чтения файла с UTF-8 кодировкой"""
        loader = FileSpecLoader()
        
        test_file = tmp_path / "test.json"
        spec_dict = {
            "openapi": "3.0.0",
            "info": {
                "title": "Тест API",
                "version": "1.0.0",
                "description": "Описание с русскими символами"
            },
            "paths": {},
            "components": {"schemas": {}}
        }
        test_file.write_text(json.dumps(spec_dict, ensure_ascii=False), encoding='utf-8')
        
        spec = loader.load(str(test_file))
        assert spec.info['title'] == "Тест API"
        assert "русскими" in spec.info['description']

