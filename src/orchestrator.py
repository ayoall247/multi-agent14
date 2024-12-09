import time
from .message_board import MessageBoard
from .agents import PlannerAgent, ResearcherAgent, CriticAgent, WriterAgent

class Orchestrator:
    def __init__(self, message_board: MessageBoard, planner: PlannerAgent, researcher: ResearcherAgent, critic: CriticAgent, writer: WriterAgent, max_cycles: int = 20):
        self.message_board = message_board
        self.planner = planner
        self.researcher = researcher
        self.critic = critic
        self.writer = writer
        self.max_cycles = max_cycles

    def run(self):
        for cycle in range(self.max_cycles):
            self.planner.act()
            self.researcher.act()
            self.critic.act()
            self.writer.act()

            print(f"\n--- Cycle {cycle+1} ---")
            for msg in self.message_board.messages:
                print(f"{msg['timestamp']:.2f} [{msg['sender']}]: {msg['content']} (tags: {msg.get('tags', [])})")

            results = [m for m in self.message_board.messages if "final_result" in m.get("tags", [])]
            if results:
                print("\nFinal result found! Stopping orchestrator.")
                break

            time.sleep(1)
