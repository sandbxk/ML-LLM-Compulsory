import os
import time
import uuid
from datetime import datetime
from typing import Tuple, Any

from autogen import ConversableAgent, UserProxyAgent

from coding_agent.config import LLM_CONFIG


def _generate_unique_filename(base_name: str, extension: str, directory: str) -> str:
    """
    Generates a unique filename based on a base name and file extension.

    :param base_name: The base name for the file.
    :param extension: The file extension (e.g., '.py').
    :return: A unique filename.
    """
    unique_id = uuid.uuid4()  # Generate a unique UUID
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{base_name}_{timestamp}_{unique_id}{extension}"
    return os.path.join(directory, filename)


def write_function(prompt: str) -> tuple[Any, str]:
    """
    Generates Python code from a given prompt and saves it to a file using a sub-agent.

    :param prompt: The task description to generate code for.
    :param coding_directory: The directory to save the generated code.
    :return: The generated code as a string.
    """

    coding_directory = "coding_directory"

    if not os.path.exists(coding_directory):
        os.makedirs(coding_directory)

    sub_agent = ConversableAgent(
        name="Code Writing Agent",
        system_message="""You are an expert Python developer. 
                              Your task is to generate a Python function based on the given description. 
                              Make sure the code is clean, well-commented, and correct.""",
        is_termination_msg=lambda msg: msg.get("content") is not None and "FINISH" in msg["content"],
        llm_config=LLM_CONFIG,
    )

    # Sub-agent to handle code generation
    user_proxy = UserProxyAgent(
        name="User",
        llm_config=False,
        is_termination_msg=lambda msg: msg.get("content") is not None and "FINISH" in msg["content"],
        human_input_mode="NEVER",
    )
    user_proxy.initiate_chat(
        recipient=sub_agent,
        max_turns=3,
        message=f'Write a Python function based on the following task: {prompt}. Return the code and end with "FINISH".'
    )

    reply = user_proxy.last_message()
    if not reply or "content" not in reply:
        raise ValueError("No reply or content found")

    # Clean the reply to get only the code
    code = reply["content"].replace("\nFINISH", "").strip()

    # unqiue name
    unique_filename = _generate_unique_filename("code_gen", ".py", coding_directory)

    # Save the generated code to a file
    with open(unique_filename, "w") as file:
        file.write(code)

    return code, unique_filename
