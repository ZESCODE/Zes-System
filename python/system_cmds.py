"""Async shell command execution."""
import asyncio
from typing import Dict, Any, Optional


class SystemCommandsSkill:
    async def run(self, command: str, shell: bool = True,
                  timeout: Optional[int] = None, env: Optional[Dict] = None,
                  cwd: Optional[str] = None) -> Dict[str, Any]:
        try:
            proc = await asyncio.create_subprocess_shell(
                command, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE, env=env, cwd=cwd,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return {
                "success": True, "returncode": proc.returncode,
                "stdout": stdout.decode("utf-8", errors="ignore"),
                "stderr": stderr.decode("utf-8", errors="ignore"),
            }
        except asyncio.TimeoutError:
            if proc:
                proc.kill()
            return {"success": False, "error": f"Command timed out after {timeout}s"}
        except Exception as e:
            return {"success": False, "error": str(e)}
