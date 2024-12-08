from .message_board import MessageBoard
from .llm_client import LLMClient
from .agents import PlannerAgent, ResearcherAgent
from .orchestrator import Orchestrator
from .utils import print_banner

def main():
    print_banner("Starting MVP Autonomous System with Grok Llama 3.3 70B")

    # Initialize core components
    board = MessageBoard()
    llm = LLMClient()

    # Initialize agents
    planner = PlannerAgent(name="Planner", message_board=board, llm_client=llm)
    researcher = ResearcherAgent(name="Researcher", message_board=board, llm_client=llm)

    # Post a user goal
    board.post_message("User", "I want a summary of recent autonomous agent goals for the industry.", tags=["user_goal"])

    # Run orchestrator loop
    orchestrator = Orchestrator(message_board=board, planner=planner, researcher=researcher)
    orchestrator.run()

    print_banner("MVP Run Complete")

if __name__ == "__main__":
    main()
