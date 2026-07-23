"""Async file/directory operations with safety checks."""
import os, json, shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
import aiofiles


class FileSystemSkill:
    async def read_text(self, path: str) -> Dict[str, Any]:
        try:
            async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                content = await f.read()
            return {"success": True, "content": content}
        except FileNotFoundError:
            return {"success": False, "error": f"File not found: {path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def write_text(self, path: str, content: str, overwrite: bool = True) -> Dict[str, Any]:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            mode = 'w' if overwrite else 'x'
            async with aiofiles.open(path, mode, encoding='utf-8') as f:
                await f.write(content)
            return {"success": True}
        except FileExistsError:
            return {"success": False, "error": f"File exists and overwrite=False: {path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def read_json(self, path: str) -> Dict[str, Any]:
        result = await self.read_text(path)
        if not result["success"]:
            return result
        try:
            data = json.loads(result["content"])
            return {"success": True, "data": data}
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Invalid JSON: {e}"}

    async def write_json(self, path: str, data: Any, indent: int = 2) -> Dict[str, Any]:
        try:
            content = json.dumps(data, indent=indent, default=str)
            return await self.write_text(path, content)
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_dir(self, path: str = ".") -> Dict[str, Any]:
        try:
            return {"success": True, "entries": os.listdir(path)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def delete(self, path: str) -> Dict[str, Any]:
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def move(self, src: str, dst: str) -> Dict[str, Any]:
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
