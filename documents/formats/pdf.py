# documents/formats/pdf.py
import tempfile
from pathlib import Path
from typing import Union

from weasyprint import HTML


def generate_pdf(
        html_content: str,
        output_filename: str,
        output_dir: Union[str, Path, None] = None
) -> str:
    """
    Конвертирует HTML-строку в PDF-файл.
    Совместимо с weasyprint==52.5
    """
    # Определяем папку для сохранения
    if output_dir is None:
        output_dir = tempfile.gettempdir()

    output_path = Path(output_dir) / output_filename

    # Конвертируем HTML → PDF
    # В версии 52.5 FontConfiguration не требуется для базовой генерации
    HTML(
        string=html_content,
        base_url=str(Path(__file__).parent)
    ).write_pdf(
        target=str(output_path),
        presentational_hints=True,
        optimize_size=('fonts', 'images')
    )

    return str(output_path)


def generate_pdf_from_file(
        template_path: Union[str, Path],
        context: dict,
        output_filename: str,
        output_dir: Union[str, Path, None] = None
) -> str:
    """
    Рендерит шаблон + конвертирует в PDF (удобный wrapper).
    """
    from documents.base import DocumentGenerator

    gen = DocumentGenerator()
    html_content = gen.render_template(template_path, context)

    return generate_pdf(html_content, output_filename, output_dir)