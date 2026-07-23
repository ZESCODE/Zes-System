"""Slack messaging via API."""
from typing import Dict, Any, List, Optional
import aiohttp


class SlackSkill:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://slack.com/api"

    async def send_message(self, channel: str, text: str,
                           blocks: Optional[List[Dict]] = None,
                           thread_ts: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {"channel": channel, "text": text, "thread_ts": thread_ts}
        if blocks:
            payload["blocks"] = blocks
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/chat.postMessage", json=payload, headers=headers) as resp:
                result = await resp.json()
                if result.get("ok"):
                    return {"success": True, "message": result}
                return {"success": False, "error": result.get("error", "Unknown error")}
