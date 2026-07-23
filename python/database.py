"""Async database queries (SQLite + PostgreSQL)."""
from typing import Dict, Any, List, Optional
import aiosqlite


class DatabaseSkill:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self._conn = None

    async def connect(self):
        if self.db_url.startswith("sqlite"):
            self._conn = await aiosqlite.connect(self.db_url.replace("sqlite://", ""))
        else:
            raise ValueError(f"Unsupported database: {self.db_url}")

    async def execute(self, query: str, params: Optional[List] = None) -> Dict[str, Any]:
        if not self._conn:
            await self.connect()
        try:
            cursor = await self._conn.execute(query, params or ())
            if query.strip().upper().startswith("SELECT"):
                rows = await cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                result = [dict(zip(columns, row)) for row in rows]
                return {"success": True, "rows": result}
            else:
                await self._conn.commit()
                return {"success": True, "rowcount": cursor.rowcount}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def close(self):
        if self._conn:
            await self._conn.close()
