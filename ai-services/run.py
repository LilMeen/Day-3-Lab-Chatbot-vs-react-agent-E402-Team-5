import uuid
import sys
from agent.react_agent import ReActAgent


def print_separator():
    print("=" * 70)


def print_react_steps(response):
    """Display the ReAct reasoning steps with all 5 fields always shown."""
    print("\n--- ReAct Reasoning Trace ---")
    for i, step in enumerate(response.steps, 1):
        print(f"\n[Step {i}]")
        print(f"  Reflection : {step.reflection or 'None'}")
        print(f"  Plan       : {step.plan or 'None'}")
        print(f"  Thought    : {step.thought or 'None'}")
        if step.action:
            print(f"  Action     : {step.action.tool}({step.action.parameters})")
        else:
            print(f"  Action     : None")
        if step.tool_result:
            result_display = step.tool_result
            print(f"  Tool Result: {result_display}")
        print(f"  Output     : {step.output or 'None'}")
    print()


def main():
    print_separator()
    print("  Movie Theater ReAct Agent - Interactive CLI")
    print("  Type 'quit' to exit, 'reset' to clear memory")
    print("  Type 'verbose on/off' to toggle reasoning trace")
    print_separator()

    agent = ReActAgent()
    session_id = str(uuid.uuid4())
    verbose = True

    print(f"\n  Session ID: {session_id}")
    print(f"  LLM Provider: {agent.provider} ({agent.model})")
    print(f"  Verbose mode: {'ON' if verbose else 'OFF'}")
    print()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("Goodbye!")
            break

        if user_input.lower() == "reset":
            agent.reset_memory(session_id)
            session_id = str(uuid.uuid4())
            print(f"Memory cleared. New session: {session_id}\n")
            continue

        if user_input.lower() == "verbose on":
            verbose = True
            print("Verbose mode: ON\n")
            continue

        if user_input.lower() == "verbose off":
            verbose = False
            print("Verbose mode: OFF\n")
            continue

        print("\nThinking...")
        try:
            response = agent.run(session_id, user_input)

            if verbose:
                print_react_steps(response)

            print_separator()
            print(f"Agent: {response.final_answer}")
            if response.tools_used:
                print(f"\n  [Tools used: {', '.join(response.tools_used)}]")
            print_separator()
            print()

        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again.\n")


if __name__ == "__main__":
    main()
