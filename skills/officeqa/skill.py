"""OfficeQA skill for grounded document reasoning.

Uses the OpenHands SDK to build an agent that answers questions
grounded in office documents (PDF, XLSX, PPTX, DOCX) from the
U.S. Treasury Bulletin corpus.
"""

from openhands.sdk import Agent, Tool
from openhands.tools import FileEditorTool, TerminalTool


def create_officeqa_agent(llm_config: dict) -> Agent:
    """Create an agent configured for the OfficeQA benchmark.

    Args:
        llm_config: LLM configuration dict with model, api_key, etc.
    """
    agent = Agent(
        llm=llm_config,
        tools=[
            Tool(name=TerminalTool.name),
            Tool(name=FileEditorTool.name),
        ],
        instructions=(
            "You are a document reasoning assistant. "
            "Answer questions by finding and citing evidence from "
            "the provided office documents. Always ground your "
            "answers in specific document passages."
        ),
    )
    return agent
