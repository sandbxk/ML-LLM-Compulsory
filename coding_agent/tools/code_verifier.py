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
    print("source_code:", source_code)

    coding_directory = os.path.dirname(code_filename)

    # Read code from file
    with open(code_filename, "r") as code_file:
        source_code = code_file.read()


    sub_agent = ConversableAgent(
        name="Test Generation Agent",
        system_message="""You are a testing expert. 
                                      Your task is to generate a test suite for a given Python function. 
                                      Ensure that the tests are comprehensive and cover edge cases.""",
        is_termination_msg=lambda msg: msg.get("content") is not None and "FINISH" in msg["content"],
        llm_config=LLM_CONFIG,
    )


    reply = sub_agent.generate_reply(
        messages=[
            {"role": "user", "content": f'Generate a unittest for the following Python function source code: \n\n{source_code}\n\n'
                                        f'Return the test code and end with "FINISH".'
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

    # Extract the test code
    test_code = reply_value

    print("TEST:", test_code)

    # Use the same base filename with '_test' appended for the test file
    test_filename = code_filename.strip().replace(".py", "_test.py")

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
