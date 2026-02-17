import argparse
import logging

from askui.web_agent import WebVisionAgent


def main() -> None:
    parser = argparse.ArgumentParser(description="AskUI Autonomous Browser CLI")
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed agent thinking"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Run command
    run_parser = subparsers.add_parser(
        "run", help="Run a single task or start interactive mode"
    )
    run_parser.add_argument(
        "task",
        nargs="?",
        help="The task to execute. If omitted, starts interactive mode.",
    )
    run_parser.add_argument("--url", help="Initial URL to navigate to")
    run_parser.add_argument(
        "--headed",
        action="store_true",
        default=True,
        help="Run in headed mode (default)",
    )
    run_parser.add_argument(
        "--headless", action="store_false", dest="headed", help="Run in headless mode"
    )

    # UI command
    ui_parser = subparsers.add_parser("ui", help="Launch the Autonomous Browser Web UI")
    ui_parser.add_argument(
        "--port", type=int, default=8000, help="Port to run the UI on"
    )
    ui_parser.add_argument("--host", default="127.0.0.1", help="Host to run the UI on")

    # Workflow command
    workflow_parser = subparsers.add_parser("workflow", help="Manage workflows")
    workflow_subparsers = workflow_parser.add_subparsers(
        dest="subcommand", help="Workflow subcommands"
    )

    record_parser = workflow_subparsers.add_parser(
        "record", help="Record a new workflow"
    )
    record_parser.add_argument("output", help="Output JSON file for the workflow")
    record_parser.add_argument("--url", help="Initial URL to start recording from")

    replay_parser = workflow_subparsers.add_parser(
        "replay", help="Replay a saved workflow"
    )
    replay_parser.add_argument("input", help="Input JSON file of the workflow")
    replay_parser.add_argument(
        "--headed",
        action="store_true",
        default=True,
        help="Run in headed mode (default)",
    )
    replay_parser.add_argument(
        "--headless", action="store_false", dest="headed", help="Run in headless mode"
    )

    args = parser.parse_args()

    # Configure logging based on verbose flag
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(message)s")

    if args.command == "run":
        run_agent(args.task, args.url, args.headed)
    elif args.command == "ui":
        launch_ui(args.host, args.port)
    elif args.command == "workflow":
        if args.subcommand == "record":
            record_workflow(args.output, args.url)
        elif args.subcommand == "replay":
            replay_workflow(args.input, not args.headed)
        else:
            workflow_parser.print_help()
    else:
        parser.print_help()


def run_agent(task: str | None, url: str | None, headed: bool) -> None:
    with WebVisionAgent(headless=not headed) as agent:
        if url:
            print(f"Navigating to {url}...")
            agent.act(f"Navigate to {url}")

        if task:
            print(f"Executing task: {task}")
            agent.act(task)
        else:
            interactive_loop(agent)


def interactive_loop(agent: WebVisionAgent) -> None:
    print("\nInteractive mode started. Type your instructions and press Enter.")
    print("Type 'exit' or 'quit' to stop.")
    while True:
        try:
            instruction = input("agent> ")
            if instruction.lower() in ["exit", "quit"]:
                break
            if not instruction.strip():
                continue
            agent.act(instruction)
        except KeyboardInterrupt:
            break
        except Exception as e:  # noqa: BLE001
            print(f"Error: {e}")


def record_workflow(output_file: str, url: str | None) -> None:
    from askui.browser.workflow_manager import WorkflowManager

    wm = WorkflowManager()
    wm.record(output_file, url)


def replay_workflow(input_file: str, headless: bool) -> None:
    from askui.browser.workflow_manager import WorkflowManager

    wm = WorkflowManager()
    wm.replay(input_file, headless)


def launch_ui(host: str, port: int) -> None:
    import uvicorn

    from askui.browser.ui.app import app

    print(f"Launching AskUI Autonomous Browser UI at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
