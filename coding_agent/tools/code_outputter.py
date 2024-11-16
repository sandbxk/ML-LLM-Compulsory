from typing import Tuple



def output_code(code: str, verification_result: Tuple[bool, str]) -> str:
    """
    Outputs the generated Python code in a code block format, with verification results.

    :param code: The generated Python code.
    :param verification_result: A tuple (bool, str) with verification status and test output.
    :return: A formatted string with the code and test results.
    """
    # Sub-agent could be added here for formatting suggestions if desired
    if verification_result[0]:
        return f"Code Generated:\n\n```\n{code}\n```\n\nTests Passed!"
    else:
        return f"Code Generated:\n\n```\n{code}\n```\n\nTests Failed:\n{verification_result[1]}"