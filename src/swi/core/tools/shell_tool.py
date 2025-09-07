import logging
import asyncio
from langchain_core.tools import tool
from langgraph.config import get_stream_writer



from enum import Enum
class SHELL(Enum):
    SHELL = "shell_tool"
    

@tool
async def shell_tool(command: str) -> str:
    """
    Run a shell command asynchronously and collect its output in real time.
    Returns: full_output (str)
    
    """
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    writer = get_stream_writer()
    output_lines = []

    
    writer("Executing Command :{command}")
    # Read stdout line by line
    while True:
        line = await process.stdout.readline()
        if not line:
            break
        decoded = line.decode().rstrip()
        output_lines.append(decoded)
        writer(decoded) 
        

    # Wait for process to finish
    await process.wait()

    # Capture stderr too (optional)
    stderr = await process.stderr.read()
    if stderr:
        output_lines.append(stderr.decode())

    return "\n".join(output_lines)
