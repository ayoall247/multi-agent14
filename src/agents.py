from typing import Optional
from .message_board import MessageBoard
from .llm_client import LLMClient
import time

class BaseAgent:
    def __init__(self, name: str, message_board: MessageBoard, llm_client: LLMClient):
        self.name = name
        self.message_board = message_board
        self.llm_client = llm_client
        self.last_read_time = 0.0

    def read_new_messages(self):
        new_msgs = self.message_board.read_messages(since=self.last_read_time)
        self.last_read_time = time.time()
        return new_msgs

    def post_message(self, content: str, tags: Optional[list] = None):
        self.message_board.post_message(self.name, content, tags)

    def think(self, prompt: str, system_prompt: str = "You are a helpful agent.", temperature: float = 0.7) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        return self.llm_client.chat_completion(messages, temperature=temperature)

    def act(self):
        pass


class PlannerAgent(BaseAgent):
    def act(self):
        new_msgs = self.read_new_messages()
        for msg in new_msgs:
            if "user_goal" in msg.get("tags", []):
                goal = msg["content"]
                subtask = f"Research this goal: {goal}"
                self.post_message(subtask, tags=["task"])


class ResearcherAgent(BaseAgent):
    def act(self):
        new_msgs = self.read_new_messages()
        for msg in new_msgs:
            if "task" in msg.get("tags", []):
                task = msg["content"]
                response = self.think(f"User asked: {task}\nPlease provide a helpful and factual answer.")
                self.post_message(response, tags=["result"])
