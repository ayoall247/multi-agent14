import time
from .message_board import MessageBoard
from .agents import PlannerAgent, ResearcherAgent

class Orchestrator:
    def __init__(self, message_board: MessageBoard, planner: PlannerAgent, researcher: ResearcherAgent, max_cycles: int = 5):
        self.message_board = message_board
        self.planner = planner
        self.researcher = researcher
        self.max_cycles = max_cycles

    def run(self):
        for cycle in range(self.max_cycles):
            self.planner.act()
            self.researcher.act()

            print(f"\n--- Cycle {cycle+1} ---")
            for msg in self.message_board.messages:
                print(f"{msg['timestamp']:.2f} [{msg['sender']}]: {msg['content']} (tags: {msg.get('tags', [])})")

            results = [m for m in self.message_board.messages if "result" in m.get("tags", [])]
            if results:
                print("\nResult found! Stopping orchestrator.")
                break

            time.sleep(1)
