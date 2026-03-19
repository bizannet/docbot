# documents/base.py
from pathlib import Path
from typing import Union, Optional
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

class DocumentGenerator:
    def __init__(self, template_dir: Optional[Union[str, Path]] = None):
        if template_dir is None:
            template_dir = Path(__file__).parent

        self.template_dir = Path(template_dir)

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )

    def render_template(self, template_path: Union[str, Path], context: dict) -> str:
        template_path = Path(template_path)
        if not template_path.is_absolute():
            template_path = self.template_dir / template_path

        try:
            template = self.env.get_template(str(template_path.relative_to(self.template_dir)))
        except (TemplateNotFound, ValueError):
            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()
            template = self.env.from_string(template_content)

        # Рендерим с контекстом
        return template.render(**context)

    def render_contract_template(self, context: dict) -> str:
        template_path = Path(__file__).parent / "contract" / "agreement" / "template.html"
        return self.render_template(template_path, context)

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        import re
        cleaned = re.sub(r'[^\w\s\.\-\u0400-\u04FF]', '_', filename)
        return cleaned.strip()