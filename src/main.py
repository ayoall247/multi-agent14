from .message_board import MessageBoard
from .llm_client import LLMClient
from .agents import PlannerAgent, ResearcherAgent, CriticAgent, WriterAgent
from .orchestrator import Orchestrator
from .utils import print_banner

def main():
    print_banner("Starting Enhanced Autonomous System with CoT, Critic, and Writer")

    # Initialize core components
    board = MessageBoard()
    llm = LLMClient()

    # Initialize agents
    planner = PlannerAgent(name="Planner", message_board=board, llm_client=llm)
    researcher = ResearcherAgent(name="Researcher", message_board=board, llm_client=llm)
    critic = CriticAgent(name="Critic", message_board=board, llm_client=llm)
    writer = WriterAgent(name="Writer", message_board=board, llm_client=llm)

    # Post a user goal - now something more complex
    board.post_message("User", "I want a polished blog post summarizing recent climate adaptation strategies in bullet points first and then refined.", tags=["user_goal"])

    # Run orchestrator loop
    orchestrator = Orchestrator(message_board=board, planner=planner, researcher=researcher, critic=critic, writer=writer)
    orchestrator.run()

    print_banner("Enhanced Run Complete")

if __name__ == "__main__":
    main()
