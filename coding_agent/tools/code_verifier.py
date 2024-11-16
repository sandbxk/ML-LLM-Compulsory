import os
import subprocess
from typing import Tuple

from autogen import ConversableAgent, UserProxyAgent

from coding_agent.config import LLM_CONFIG


def verify_function(source_code: str, code_filename: str) -> Tuple[bool, str]:
    """
    Verifies the generated Python function by running a set of predefined tests.


    :param source_code: The source code of the function to test.
    :param code_filename: The filename of the source code file.
    :param coding_directory: The directory where the source code file is saved.
    :return: A tuple (bool, str) where the first element indicates if tests passed, and the second is the output.
    """

    coding_directory = os.path.dirname(code_filename)

    sub_agent = ConversableAgent(
        name="Test Generation Agent",
        system_message="""You are a testing expert. 
                                      Your task is to generate a test suite for a given Python function. 
                                      Ensure that the tests are comprehensive and cover edge cases.""",
        is_termination_msg=lambda msg: msg.get("content") is not None and "FINISH" in msg["content"],
        llm_config=LLM_CONFIG,
    )

    # Sub-agent to handle test generation, with access to the function's source code
    user_proxy = UserProxyAgent(
        name="User",
        llm_config=False,
        is_termination_msg=lambda msg: msg.get("content") is not None and "FINISH" in msg["content"],
        human_input_mode="NEVER",
    )
    user_proxy.initiate_chat(
        recipient=sub_agent,
        max_turns=3,
        message=f'Generate a unittest for the following Python function source code: \n\n{source_code}\n\n'
                f'Return the test code and end with "FINISH".'
    )

    reply = user_proxy.last_message()
    if not reply or "content" not in reply:
        raise ValueError("No reply or content found")

    # Extract the test code
    test_code = reply["content"].replace("\nFINISH", "").strip()

    # Use the same base filename with '_test' appended for the test file
    test_filename = code_filename.replace(".py", "_test.py")

    # Ensure the coding directory exists
    if not os.path.exists(coding_directory):
        os.makedirs(coding_directory)

    # Save the test suite to a file
    with open(test_filename, "w") as test_file:
        test_file.write(test_code)

    # Execute the test suite
    try:
        result = subprocess.run(["python", test_filename], check=True, capture_output=True, text=True)
        test_output = result.stdout
        passed = True
    except subprocess.CalledProcessError as e:
        test_output = e.stdout + "\n" + e.stderr
        passed = False

    return passed, test_output
