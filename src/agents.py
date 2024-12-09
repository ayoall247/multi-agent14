from typing import Optional
from .message_board import MessageBoard
from .llm_client import LLMClient
import time
import json

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
        """
        Encourage chain-of-thought:
        We'll instruct the model to reason step-by-step. The model may not show the reasoning,
        but will be guided internally.

        Example prompt strategy:
        - System prompt: Remind the model to think step-by-step and produce final answers clearly.
        - User prompt: The actual request with instructions.
        """
        messages = [
            {"role": "system", "content": system_prompt + " Please think step-by-step, reason carefully, and then produce a final concise answer."},
            {"role": "user", "content": prompt}
        ]
        return self.llm_client.chat_completion(messages, temperature=temperature)

    def act(self):
        pass


class PlannerAgent(BaseAgent):
    """
    The planner breaks the user goal into a sequence of tasks:
    1. Research the goal (task: 'research_task')
    2. Critically review the research (task: 'critic_task')
    3. Produce a final polished output (task: 'writer_task')

    We'll implement a simple logic:
    - When it sees a user_goal, it posts a research_task.
    - When the research_task is completed (result found), it posts a critic_task.
    - When the critic_task is completed (critic approves), it posts a writer_task.
    """
    def act(self):
        new_msgs = self.read_new_messages()

        # Check if we already posted certain tasks by looking at messages
        user_goals = [m for m in self.message_board.messages if "user_goal" in m.get("tags", [])]
        research_results = [m for m in self.message_board.messages if "research_result" in m.get("tags", [])]
        critic_approval = [m for m in self.message_board.messages if "critic_approved" in m.get("tags", [])]
        final_results = [m for m in self.message_board.messages if "final_result" in m.get("tags", [])]

        # If we have a user goal but no research_task posted yet:
        if user_goals and not any("research_task" in m.get("tags", []) for m in self.message_board.messages):
            goal = user_goals[-1]["content"]
            task = f"Please research this goal: {goal}"
            self.post_message(task, tags=["research_task"])
            return

        # If we have research_result but no critic_task posted yet:
        if research_results and not any("critic_task" in m.get("tags", []) for m in self.message_board.messages):
            # The critic should evaluate the research result
            self.post_message("Please evaluate the research results for correctness and completeness.", tags=["critic_task"])
            return

        # If critic_approved but no writer_task posted yet:
        if critic_approval and not any("writer_task" in m.get("tags", []) for m in self.message_board.messages) and not final_results:
            self.post_message("Please produce a polished, final report suitable for publication.", tags=["writer_task"])
            return


class ResearcherAgent(BaseAgent):
    """
    The researcher picks up a 'research_task' and returns JSON-structured data.
    The researcher tries to produce bullet points of factual info in JSON.
    """
    def act(self):
        new_msgs = self.read_new_messages()
        for msg in new_msgs:
            if "research_task" in msg.get("tags", []):
                task = msg["content"]
                # Prompt the LLM for structured JSON output
                prompt = (
                    f"{task}\n\n"
                    "Instructions: Return findings in JSON format. Include a 'facts' key with a list of bullet points.\n"
                    "Example:\n{\n  \"facts\": [\n    \"Bullet point 1\",\n    \"Bullet point 2\"\n  ]\n}"
                )
                response = self.think(prompt, system_prompt="You are a research assistant.")
                # Validate JSON
                # If invalid JSON, just wrap it as is. Ideally, we'd retry until valid.
                try:
                    data = json.loads(response)
                    if "facts" not in data:
                        # If no 'facts', just add a fallback
                        data = {"facts": [response]}
                except json.JSONDecodeError:
                    data = {"facts": [response]}

                final_response = json.dumps(data, indent=2)
                self.post_message(final_response, tags=["research_result"])


class CriticAgent(BaseAgent):
    """
    The critic picks up 'critic_task' and evaluates the research_result for correctness.
    If unsatisfactory, requests revision by posting a new research_task.
    If good, posts 'critic_approved'.
    """
    def act(self):
        new_msgs = self.read_new_messages()
        for msg in new_msgs:
            if "critic_task" in msg.get("tags", []):
                # Find the latest research_result
                research_msgs = [m for m in self.message_board.messages if "research_result" in m.get("tags", [])]
                if not research_msgs:
                    # No research result? Critic can't proceed
                    continue
                latest_research = research_msgs[-1]["content"]

                prompt = (
                    "You are a critic. You have research results:\n"
                    f"{latest_research}\n\n"
                    "Evaluate correctness, clarity, and completeness. If good, say 'APPROVED'. If not, say 'REVISE' and provide guidance."
                )
                response = self.think(prompt, system_prompt="You are a critical evaluator. Be concise.")
                if "APPROVED" in response.upper():
                    self.post_message("Research is satisfactory.", tags=["critic_approved"])
                else:
                    # If revise, request new research
                    self.post_message("Please revise the research with more accurate or additional details.", tags=["research_task"])


class WriterAgent(BaseAgent):
    """
    The writer picks up 'writer_task', uses the final approved research result,
    and produces a polished final output (like a short report).
    """
    def act(self):
        new_msgs = self.read_new_messages()
        for msg in new_msgs:
            if "writer_task" in msg.get("tags", []):
                # Get the latest research_result and assume it's approved
                research_msgs = [m for m in self.message_board.messages if "research_result" in m.get("tags", [])]
                critic_approval = [m for m in self.message_board.messages if "critic_approved" in m.get("tags", [])]
                if not research_msgs or not critic_approval:
                    # Without research or approval, we cannot proceed
                    continue

                latest_research = research_msgs[-1]["content"]
                prompt = (
                    "You are a professional writer. You have approved research (in JSON) below:\n"
                    f"{latest_research}\n\n"
                    "Use the facts from the JSON to write a polished, engaging, and informative final report. "
                    "The report should be well-structured, with a clear introduction, body, and conclusion. "
                    "Do not include JSON in the final output.\n"
                    "Think step-by-step internally, then produce the final report."
                )
                response = self.think(prompt, system_prompt="You are a skilled writer and communicator.")
                # Post final result
                self.post_message(response, tags=["final_result"])
