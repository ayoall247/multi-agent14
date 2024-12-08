from typing import List, Dict, Optional
from .utils import current_timestamp

class MessageBoard:
    def __init__(self):
        self.messages: List[Dict] = []

    def post_message(self, sender: str, content: str, tags: Optional[List[str]] = None):
        msg = {
            "sender": sender,
            "content": content,
            "tags": tags if tags else [],
            "timestamp": current_timestamp()
        }
        self.messages.append(msg)

    def read_messages(self, since: float = 0.0) -> List[Dict]:
        return [m for m in self.messages if m["timestamp"] > since]

    def filter_messages(self, keyword: str = None, tag: str = None, since: float = 0.0) -> List[Dict]:
        msgs = self.read_messages(since)
        if keyword:
            msgs = [m for m in msgs if keyword.lower() in m["content"].lower()]
        if tag:
            msgs = [m for m in msgs if tag in m["tags"]]
        return msgs
