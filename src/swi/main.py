# backend/react_agent.py

import asyncio
from typing import Optional

import pyfiglet
from pydantic import BaseModel
from rich.console import Console

from langchain_core.messages import HumanMessage
from swi.core.builder import CodingAgent
from dotenv import load_dotenv
from swi.core.prompt import get_prompt
# Initialize Rich console for colored outputs
console = Console()

# Global placeholders for agent and client (if needed later)
agent = None
mcp_client = None
ENV_FILE = ".env"
load_dotenv(ENV_FILE)
# -------------------------------
# Pydantic model for queries
# -------------------------------
class Query(BaseModel):
    message: str
    thread_id: Optional[str]


# -------------------------------
# Helper functions
# -------------------------------
def get_thread() -> str:
    """
    Return a thread ID for conversation.
    Currently static, can be extended to dynamic/thread management.
    """
    return "1"


# -------------------------------
# Main async agent loop
# -------------------------------
async def run_graph():
    """
    Main entry point to start the CodingAgent in interactive mode.
    Loads MCP tools, builds the agent, and interacts with user input.
    """    
    # Build the agent graph
    graph = await CodingAgent().builder()

    # Display ASCII banner
    ascii_art = pyfiglet.figlet_format("SWE", font="block")
    console.print(f"[bold cyan]{ascii_art}[/bold cyan]")
    console.print("[bold green]Agent Ready![/bold green]")

    # Interactive input loop
    config = {"configurable": {"thread_id": "1"}} 
    while True:
        text_input = input("> ").strip()

        if text_input.lower() == "exit":
            console.print("[red]Exiting agent...[/red]")
            break
        
        
        # Pass user input to agent 
        async for type, content in graph.astream(
            input={"messages": HumanMessage(text_input), "context": get_prompt()},
            config=config,
            stream_mode=["messages","custom"],
            kwargs = {"recursionLimit": 200}
            
        ):
            
            if type == "messages":
                content, metadata = content
                console.print(content.content, style="cyan", end="")
            else:
                console.print(content, style="magenta")


# -------------------------------
# Entry point
# -------------------------------
def main():
    # Run the asnc event loop
    try:
        from swi.utils.model import ModelLoader
        ModelLoader().check()
    except Exception as e:  # noqa: F841
        console.print_exception() 
    asyncio.run(run_graph())
