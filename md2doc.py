import os
import sys
import click
from io import BytesIO

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
    
    # Поддержка .doc через RTF-конвертацию
    if output_ext == "doc":
        output_ext = "rtf"
        click.secho("Внимание: Pandoc не поддерживает прямой вывод в .doc. Используем RTF-формат.", fg='yellow')
    
    # Конвертируем
    pypandoc.convert_text(
        md_content,
        output_ext,
        format="md",
        outputfile=output_path,
        extra_args=["--standalone"]
    )

@click.command()
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
def main(input, output, engine):
    """
    Конвертер Markdown в DOC/DOCX
    
    Примеры:
    
    \b
      md2doc input.md output.docx
      md2doc input.md output.doc --engine=pandoc
    """
    
    # Проверка расширений файлов
    if not input.lower().endswith(".md"):
        click.secho("Ошибка: входной файл должен иметь расширение .md", fg='red')
        sys.exit(1)
    
    if not output.lower().endswith((".docx", ".doc")):
        click.secho("Ошибка: выходной файл должен быть .docx или .doc", fg='red')
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
            convert_with_pandoc(md_content, output)
            
            # Переименование RTF в DOC
            if output_ext == ".doc" and os.path.exists(output):
                new_output = os.path.splitext(output)[0] + ".doc"
                os.rename(output, new_output)
                click.secho(f"✓ Успешно! Конвертировано через Pandoc -> {new_output}", fg='green')
            else:
                click.secho(f"✓ Успешно! Конвертировано через Pandoc -> {output}", fg='green')
    
    except Exception as e:
        click.secho(f"\nОшибка конвертации ({engine}): {e}", fg='red')
        if "pandoc" in str(e).lower():
            click.secho("\nУбедитесь что установлен Pandoc: https://pandoc.org/installing.html", fg='yellow')
        sys.exit(1)

if __name__ == "__main__":
    main()