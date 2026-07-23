"""PDF generation from HTML or URL using WeasyPrint."""
import os
from typing import Dict, Any, Optional, List
from weasyprint import HTML


class PDFGenerationSkill:
    async def from_html(self, html_content: str, output_path: str,
                        stylesheets: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            HTML(string=html_content).write_pdf(output_path, stylesheets=stylesheets, **kwargs)
            return {"success": True, "path": output_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def from_url(self, url: str, output_path: str, **kwargs) -> Dict[str, Any]:
        try:
            HTML(url=url).write_pdf(output_path, **kwargs)
            return {"success": True, "path": output_path}
        except Exception as e:
            return {"success": False, "error": str(e)}
