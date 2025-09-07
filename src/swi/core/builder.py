from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode
from swi.utils.model import ModelLoader
from langchain_core.messages import SystemMessage
from swi.core.prompt import compress_prompt , get_prompt
from langgraph.checkpoint.memory import InMemorySaver
from rich.console import Console
from typing import Literal
from langgraph.types import Command
from swi.core.tools.file_tool import get_file_content,edit_file, write_file_tool, note_pad
from swi.core.tools.shell_tool import shell_tool
from swi.core.tools.fetch_tool import fetch_url_content
from langgraph.graph import MessagesState

console = Console()

checkpointer = InMemorySaver()

class ContextState(MessagesState):
    context: str


class CodingAgent:
    def __init__(self):
        self.tools = [
            get_file_content,
            write_file_tool,
            edit_file,
            note_pad,
            fetch_url_content,
            shell_tool,
        ]
        self.model = ModelLoader().load()

    async def compress_context(self, state: ContextState):
        """Compress the Messages"""
        messages = state.get("messages", [])
        summary = self.model.invoke([SystemMessage(compress_prompt)] + messages)
        return {"context": state.get("context")+ "\n"+ summary}

    async def conditional_node(
        self,
        state: ContextState,
        messages_key: str = "messages",
    ) -> Command[Literal["tools", "call_model"]]:
        """Conditional Node"""

        if len(state.get(messages_key,[]))>15:
            return Command(goto=compress_prompt)
        if isinstance(state, list):
            ai_message = state[-1]
        elif isinstance(state, dict) and (messages := state.get(messages_key, [])):
            ai_message = messages[-1]
        elif messages := getattr(state, messages_key, []):
            ai_message = messages[-1]
        else:
            raise ValueError(f"No messages found in input state to tool_edge: {state}")
        if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
            return Command(goto="tools", update={"context": get_prompt()})


        return Command(goto="__end__")

    async def call_model(self, state: ContextState):
        response = self.model.bind_tools(self.tools).invoke(
            [SystemMessage(state.get("context", ""))] + state.get("messages", [])
        )
        print(state.get("messages"))
        return {"messages": response}

    async def builder(self):
        """Builds Graph"""
        builder = StateGraph(ContextState)

        builder.add_node("call_model", self.call_model)
        builder.add_node("tools", ToolNode(self.tools))
        builder.add_node("conditional_node", self.conditional_node)

        # Order: START -> context -> model
        builder.add_edge(START, "call_model")
        builder.add_edge("call_model", "conditional_node")
        builder.add_edge("conditional_node","tools")
        builder.add_edge("conditional_node","__end__")
        builder.add_edge("tools", "call_model")

        return builder.compile(checkpointer=checkpointer)
