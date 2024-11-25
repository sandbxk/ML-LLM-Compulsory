import os
import time
import uuid
from datetime import datetime
from typing import Tuple, Any

from autogen import ConversableAgent, UserProxyAgent
from flaml.autogen import AssistantAgent

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

    sub_agent = AssistantAgent(
        name="Code Writing Agent",
        system_message="""You are an expert Python developer. 
                              Your task is to generate a Python function based on the given description. 
                              Make sure the code is clean, well-commented, and correct. You do not write anything apart from the code. 
                              The code should be ready to be copied and pasted into a Python file, so do not use code-blocks either.""",
        is_termination_msg=lambda msg: msg.get("content") is not None and "FINISH" in msg["content"],
        llm_config=LLM_CONFIG,
        human_input_mode="NEVER"
    )


    reply = sub_agent.generate_reply(
        messages=[
            {"role": "user", "content": f'Write a Python function based on the following task: {prompt}. '
                                        f'Do not write anything apart from the code. And do not use code-blocks. Or any none-code text '},
        ],
    )

    if not reply:
        raise ValueError("No reply found")

    reply_value = ""
    if isinstance(reply, dict):
        reply_content = reply["content"]
        if reply_content:
            reply_value = reply_content
        else:
            raise ValueError("No content found in the reply")
    else:
        reply_value = reply

    reply_value = reply_value.replace("\nFINISH", "").strip()

    code = reply_value

    # Remove ```python code blocks
    code = code.replace("```python", "").replace("```", "").strip()


    # Save the generated code to a file
    code_filename = _generate_unique_filename("generated_code", ".py", coding_directory)
    with open(code_filename, "w") as file:
        file.write(code)

    return code, code_filename

