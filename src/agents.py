# src/agents.py
import json
import time
from typing import Optional
from .message_board import MessageBoard
from .llm_client import LLMClient

def build_context(all_msgs):
    # Build a text summary of all user goals and final results so far
    user_goals = [m for m in all_msgs if "user_goal" in m.get("tags",[])]
    final_results = [m for m in all_msgs if "final_result" in m.get("tags",[])]
    convo_text = ""
    for g in user_goals:
        convo_text += f"User asked: {g['content']} \n"
        fr = [x for x in final_results if x['timestamp'] > g['timestamp']]
        if fr:
            convo_text += f"Answer: {fr[-1]['content']}\n"
    return convo_text.strip()

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

    def think(self, prompt: str, system_prompt: str = "You are a helpful agent.", temperature: float = 0.7, add_context: bool = True) -> str:
        all_msgs = self.message_board.get_all_messages()
        context_text = build_context(all_msgs) if add_context else ""
        full_prompt = (context_text + "\n\n" + prompt).strip() if context_text else prompt

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
        ]
        response = self.llm_client.chat_completion(messages, temperature=temperature)
        response = response.replace("```", "").strip()
        # collapse multiple spaces/newlines
        response = ' '.join(response.split())
        return response

    def act(self):
        pass

class PlannerAgent(BaseAgent):
    # same logic as before
    def act(self):
        new_msgs = self.read_new_messages()
        all_msgs = self.message_board.get_all_messages()

        user_goals = [m for m in all_msgs if "user_goal" in m.get("tags", [])]
        final_results = [m for m in all_msgs if "final_result" in m.get("tags", [])]
        incomplete_goals = [g for g in user_goals if g['timestamp'] > max((f['timestamp'] for f in final_results), default=0)]

        if incomplete_goals:
            latest_goal = incomplete_goals[-1]
            research_task_posted = any(m['timestamp'] > latest_goal['timestamp'] and "research_task" in m.get("tags",[]) for m in all_msgs)
            critic_approved = any(m['timestamp'] > latest_goal['timestamp'] and "critic_approved" in m.get("tags",[]) for m in all_msgs)
            final_result_exists = any(m['timestamp'] > latest_goal['timestamp'] and "final_result" in m.get("tags",[]) for m in all_msgs)
            
            if not research_task_posted and not final_result_exists:
                self.post_message(f"Please research this goal: {latest_goal['content']}", tags=["research_task"])
            elif research_task_posted and not critic_approved and not final_result_exists:
                research_results = [mm for mm in all_msgs if "research_result" in mm.get("tags", []) and mm["timestamp"] > latest_goal["timestamp"]]
                if research_results and not any("critic_task" in mm.get("tags",[]) for mm in all_msgs if mm["timestamp"]>latest_goal["timestamp"]):
                    self.post_message("Please evaluate the research results.", tags=["critic_task"])
            elif critic_approved and not final_result_exists:
                if not any("writer_task" in mm.get("tags", []) for mm in all_msgs if mm["timestamp"]>latest_goal["timestamp"]):
                    self.post_message("Produce a final polished report.", tags=["writer_task"])

class ResearcherAgent(BaseAgent):
    def act(self):
        new_msgs = self.read_new_messages()
        for msg in new_msgs:
            if "research_task" in msg.get("tags", []):
                task = msg["content"]
                prompt = (
                    f"{task}\n\n"
                    "Provide a short, plain text summary (a few sentences) of key info. No code, no bullet points."
                )
                research = self.think(prompt, system_prompt="You are a research assistant. Plain text.", add_context=True)
                self.post_message(research, tags=["research_result"])

                # produce resources_result
                prompt_links = (
                    f"Given the topic: '{task}', list a few relevant helpful websites or sources as a list of URLs separated by spaces. Plain text only."
                )
                resources = self.think(prompt_links, system_prompt="You only output URLs separated by spaces.", add_context=False)
                resources = ' '.join(resources.split())
                self.post_message(resources, tags=["resources_result"])

class CriticAgent(BaseAgent):
    def act(self):
        new_msgs = self.read_new_messages()
        for msg in new_msgs:
            if "critic_task" in msg.get("tags", []):
                self.post_message("Research is satisfactory.", tags=["critic_approved"])

class WriterAgent(BaseAgent):
    def act(self):
        new_msgs = self.read_new_messages()
        for msg in new_msgs:
            if "writer_task" in msg.get("tags", []):
                all_msgs = self.message_board.get_all_messages()
                latest_goal_ts = max(m['timestamp'] for m in all_msgs if "user_goal" in m.get("tags", []))
                research = [m for m in all_msgs if "research_result" in m.get("tags",[]) and m['timestamp']>latest_goal_ts]
                resources = [m for m in all_msgs if "resources_result" in m.get("tags",[]) and m['timestamp']>latest_goal_ts]
                critic_approved = [m for m in all_msgs if "critic_approved" in m.get("tags",[]) and m['timestamp']>latest_goal_ts]

                if research and critic_approved:
                    latest_research = research[-1]['content']
                    latest_resources = resources[-1]['content'] if resources else ""

                    # We'll produce HTML:
                    # A short paragraph: <p> ... </p>
                    # Followed by links in bullet form: <ul><li><a href='URL'>URL</a></li></ul>
                    # Follow-ups also bullet form.
                    prompt = (
                        "You are a writer. Given this research:\n"
                        f"{latest_research}\n\n"
                        "Produce a concise, plain-text paragraph summarizing essential insights. Not too short, not too long.\n"
                        "Then provide a small list of helpful relevant links from the resources as clickable HTML links.\n"
                        "Finally, suggest a few potential follow-up questions as another bullet list.\n"
                        "Format:\n"
                        "<p>Main answer text here.</p>\n"
                        "<p>Helpful Links:</p>\n"
                        "<ul><li><a href='URL1' target='_blank'>URL1</a></li><li><a href='URL2' ...>URL2</a></li></ul>\n"
                        "<p>Potential Follow-ups:</p>\n"
                        "<ul><li>Question 1</li><li>Question 2</li></ul>\n"
                        "Use the resources provided: " + latest_resources
                    )
                    response = self.think(prompt, system_prompt="You are a careful writer. Output valid HTML as described.", add_context=True)
                    self.post_message(response.strip(), tags=["final_result"])

class SummarizerAgent(BaseAgent):
    def __init__(self, name: str, message_board: MessageBoard, llm_client: LLMClient):
        super().__init__(name, message_board, llm_client)

    def act(self):
        all_msgs = self.message_board.get_all_messages()
        final_results = [m for m in all_msgs if "final_result" in m.get("tags",[])]
        if final_results:
            user_goals = [m for m in all_msgs if "user_goal" in m.get("tags",[])]
            convo_text = ""
            for g in user_goals:
                convo_text += f"User goal: {g['content']} "
                fr = [x for x in final_results if x['timestamp'] > g['timestamp']]
                if fr:
                    convo_text += f"Final result: {fr[-1]['content']} "

            prompt = (
                "Summarize the entire conversation (all user goals and their final results) into one concise paragraph. "
                "No code, no bullet points, just a plain summary."
            )
            summary = self.think(prompt, system_prompt="You are a summarizer.", temperature=0.5, add_context=False)
            summary = ' '.join(summary.split())
            self.post_message(summary, tags=["summary_message"])
