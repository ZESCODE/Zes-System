"""OCR text extraction from images using Tesseract."""
from typing import Dict, Any, Optional
import pytesseract
from PIL import Image
import io


class OCRSkill:
    def __init__(self, tesseract_cmd: Optional[str] = None):
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    async def extract_text(self, image_data: bytes, language: str = "eng",
                           preprocessing: Optional[str] = None) -> Dict[str, Any]:
        try:
            img = Image.open(io.BytesIO(image_data))
            if preprocessing == "grayscale":
                img = img.convert("L")
            text = pytesseract.image_to_string(img, lang=language)
            return {"success": True, "text": text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def extract_from_path(self, image_path: str, **kwargs) -> Dict[str, Any]:
        try:
            with open(image_path, "rb") as f:
                return await self.extract_text(f.read(), **kwargs)
        except Exception as e:
            return {"success": False, "error": str(e)}
