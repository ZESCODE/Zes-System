"""SSH remote command execution via asyncssh."""
from typing import Dict, Any, Optional
import asyncssh


class SSHSkill:
    def __init__(self, host: str, username: str, password: Optional[str] = None,
                 key_file: Optional[str] = None):
        self.host = host
        self.username = username
        self.password = password
        self.key_file = key_file
        self._conn = None

    async def connect(self):
        try:
            self._conn = await asyncssh.connect(
                self.host, username=self.username, password=self.password,
                client_keys=[self.key_file] if self.key_file else None,
            )
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def exec_command(self, command: str) -> Dict[str, Any]:
        if not self._conn:
            result = await self.connect()
            if not result["success"]:
                return result
        try:
            result = await self._conn.run(command, check=False)
            return {"success": True, "stdout": result.stdout,
                    "stderr": result.stderr, "exit_code": result.exit_status}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def close(self):
        if self._conn:
            self._conn.close()
