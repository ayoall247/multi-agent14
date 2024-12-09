# src/orchestrator.py
import time

class Orchestrator:
    def __init__(self, message_board, planner, researcher, critic, writer, summarizer, max_cycles=3):
        self.message_board = message_board
        self.planner = planner
        self.researcher = researcher
        self.critic = critic
        self.writer = writer
        self.summarizer = summarizer
        self.max_cycles = max_cycles

    def run(self):
        for cycle in range(self.max_cycles):
            self.planner.act()
            self.researcher.act()
            self.critic.act()
            self.writer.act()
            self.summarizer.act()

            print(f"\n--- Cycle {cycle+1} ---")
            all_msgs = self.message_board.get_all_messages()
            for msg in all_msgs:
                print(f"{msg['timestamp']:.2f} [{msg['sender']}]: {msg['content']} (tags: {msg.get('tags', [])})")

            final_results = [m for m in all_msgs if "final_result" in m.get("tags", [])]
            if final_results:
                print("\nFinal result found! Stopping orchestrator.")
                break

            time.sleep(1)
