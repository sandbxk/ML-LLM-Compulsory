import ast
import os

from autogen import AssistantAgent, UserProxyAgent, ChatResult, register_function
from autogen.coding import LocalCommandLineCodeExecutor

from coding_agent.config import LLM_CONFIG
from coding_agent.tools.code_outputter import output_code
from coding_agent.tools.code_verifier import verify_function
from coding_agent.tools.code_writer import write_function

Coding_directory = "coding_directory"

ReAct_prompt = """
You are an expert Python coding assistant. Your task is to solve programming challenges by writing Python code, verifying its correctness, and presenting the final solution.

You have access to several tools to help you accomplish this:

- **write_python_function**: Generates a Python function based on a coding task description.
- **verify_python_function**: Verifies the generated Python code by running tests and provides the results.
- **output_python_code**: Outputs the generated Python code in a code block format along with test verification results.

Use the following format:

Question: the coding task you need to solve
Thought: carefully consider what needs to be done and which tool to use first
Action: the action you need to take using one of the provided tools
Action Input: the input to the action, such as a task description or function name
Observation: the result of the action based on the tool's output
... (this thought/action/action input/observation sequence can repeat as many times as necessary)
Thought: I now have the final solution, which has been verified
Final Answer: the final Python code solution, verified, formatted, and ready for presentation

Begin! DO NOT BREAK AWAY FROM THIS FORMAT.
Question: {input}
"""

def react_prompt_message(sender, recipient, context):
    """
    Return the ReAct prompt message interpolated with the input question.
    """
    return ReAct_prompt.format(input=context["question"])


def create_coding_agent() -> AssistantAgent:
    """
    Return a new coding agent.
    """
    agent = AssistantAgent(
        name="Coding Assistant",
        system_message=f"""
        You are an AI assistant for writing and verifying Python code. Your task is to:
        1. Write Python functions based on the provided prompts.
        2. Write tests to ensure the validity of the code. Ensure the function passes predefined tests.
        3. If tests are provided, write test cases and save them in the coding directory as well.
      

        Only use tools to interact with the environment and the code. Don't try to reason or generate content outside the scope of the task.
        You are only done when the tests pass and the code is correct.
        If you are done with the task, reply with "TERMINATE".
        """,
        llm_config=LLM_CONFIG
    )

    return agent

def create_user_proxy(code_executor: LocalCommandLineCodeExecutor):
    """
    Return a new user proxy agent.
    """
    user_proxy = UserProxyAgent(
        name="User",
        llm_config=False,
        is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().lower().endswith("terminate"),
        human_input_mode="NEVER",
        max_consecutive_auto_reply=10,
        code_execution_config={
            "executor": code_executor
        },
    )
    return user_proxy


def create_local_code_executor():
    """
    Return a new local code executor.
    """
    return LocalCommandLineCodeExecutor(
        timeout=100,
    )


def setup_agents1():
    """
    Setup the agents.
    """
    # Create the code executor, user proxy, and feedback analysis agent
    code_executor = create_local_code_executor()
    user_proxy = create_user_proxy(code_executor)
    coding_agent = create_coding_agent()



    # Add the feedback reader tool to the feedback analysis agent and user proxy agent
    register_function(
        write_function,
        caller=coding_agent,
        executor=user_proxy,
        name="write_python_function",
        description="Generates a Python function based on a task prompt and saves it to a file.",
    )

    # Add the sentiment analysis tool to the feedback analysis agent and user proxy agent
    register_function(
        verify_function,
        caller=coding_agent,
        executor=user_proxy,
        name="verify_python_function",
        description="Verifies the generated Python function by running predefined tests."
    )


    # Add the calculate average tool to the feedback analysis agent and user proxy agent
    register_function(
        output_code,
        caller=coding_agent,
        executor=user_proxy,
        name="output_python_code",
        description="Outputs the generated Python code in a code block format along with test verification results."
    )


    # Return the user proxy and feedback analysis agent
    return user_proxy, coding_agent


def setup_agents():
    """
    Setup the agents.
    """
    # Create the code executor, user proxy, and feedback analysis agent
    code_executor = create_local_code_executor()
    user_proxy = create_user_proxy(code_executor)
    coding_agent = create_coding_agent()



    # Add the feedback reader tool to the feedback analysis agent and user proxy agent
    register_function(
        write_function,
        caller=coding_agent,
        executor=user_proxy,
        name="write_python_function",
        description="Generates a Python function based on a task prompt.",
    )

    # Add the sentiment analysis tool to the feedback analysis agent and user proxy agent
    register_function(
        verify_function,
        caller=coding_agent,
        executor=user_proxy,
        name="verify_python_function",
        description="Verifies a Python function by generating tests and running them."
    )


    # Add the calculate average tool to the feedback analysis agent and user proxy agent
    register_function(
        output_code,
        caller=coding_agent,
        executor=user_proxy,
        name="output_python_code",
        description="Outputs the generated Python code in a code block format along with test verification results."
    )


    # Return the user proxy and feedback analysis agent
    return user_proxy, coding_agent


def get_tool_calls(chat_result: ChatResult):
    """
    Return the tool calls from the chat result.
    """
    tool_call_history = []

    for message in chat_result.chat_history:
        if "tool_calls" in message.keys():
            tool_calls = map(lambda x: { "name": x["function"]["name"], "arguments": ast.literal_eval(x["function"]["arguments"]) }, message["tool_calls"])
            tool_call_history.extend(list(tool_calls))

    return tool_call_history


def find_final_answer(chat_result: ChatResult):
    """
    Return the final answer from the chat result.
    """

    # Get the chat history
    messages = chat_result.chat_history
    final_answer = None

    # Iterate over the chat history in reverse order
    for message in reversed(messages):
        # Check if the message contains the final answer
        if "final answer:" in message.get("content", "").lower():
            # Get the final answer block    
            final_answer_block = message.get("content", "")

            # Split the final answer block into lines
            answer_block_lines = final_answer_block.split("\n")

            # Get the final answer
            final_answer = answer_block_lines[-1].split("Final Answer:")[1].strip()
            break

    # Return the final answer
    return final_answer


def main():
    os.environ["AUTOGEN_USE_DOCKER"] = "False"

    # Setup the agents
    user_proxy, coding_agent = setup_agents()

    # Define the task
    task = "Write a Python function that takes a list of numbers and returns the average of the numbers."

    # Initiate the chat
    chat = user_proxy.initiate_chat(
        coding_agent,
        message=react_prompt_message,
        question=task
    )

    # Get the final answer
    #final_answer = find_final_answer(chat)

    # Get the tool calls
    tool_calls = get_tool_calls(chat)

    # Print the final answer and tool calls
    #print("Final Answer:", final_answer)
    print("Tool Calls:", tool_calls)



if __name__ == "__main__":
    main()
