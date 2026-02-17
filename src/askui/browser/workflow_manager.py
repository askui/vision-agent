import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from askui.tools.testing.scenario_models import Scenario, ScenarioStep
from askui.utils.datetime_utils import now
from askui.utils.id_utils import generate_time_ordered_id
from askui.web_agent import WebVisionAgent

logger = logging.getLogger(__name__)


class WorkflowManager:
    def record(self, output_file: str, initial_url: str = None):
        """
        Interactively record a sequence of instructions and save them as a Scenario.
        """
        steps = []
        print(f"\n--- Recording workflow to {output_file} ---")

        if initial_url:
            print(f"Adding initial step: Navigate to {initial_url}")
            steps.append(
                ScenarioStep(keyword="Given", text=f"I navigate to {initial_url}")
            )

        print("Enter instructions for the agent one by one.")
        print(
            "Special commands: 'save' to finish, 'cancel' to abort, 'undo' to remove "
            "last step."
        )

        while True:
            try:
                instruction = input("record> ").strip()
                if not instruction:
                    continue

                if instruction.lower() == "save":
                    if not steps:
                        print("No steps recorded. Nothing to save.")
                        return
                    break

                if instruction.lower() == "cancel":
                    print("Recording cancelled.")
                    return

                if instruction.lower() == "undo":
                    if steps:
                        removed = steps.pop()
                        print(f"Removed: {removed.text}")
                    else:
                        print("Nothing to undo.")
                    continue

                # Add as a "When" step
                steps.append(ScenarioStep(keyword="When", text=instruction))
                print(f"Added: {instruction}")

            except KeyboardInterrupt:
                print("\nRecording interrupted.")
                return

        # Create the Scenario object
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        scenario = Scenario(
            id=generate_time_ordered_id("scen"),
            feature="feat_recorded",  # Default feature ID for recorded workflows
            name=f"Recorded Workflow {timestamp}",
            steps=steps,
            created_at=now(),
        )

        # Save to file
        with Path(output_file).open("w") as f:
            f.write(scenario.model_dump_json(indent=2))

        print(f"\nSuccessfully saved {len(steps)} steps to {output_file}")

    def replay(self, input_file: str, headless: bool = False):
        """
        Load a Scenario from a JSON file and execute its steps using WebVisionAgent.
        """
        print(f"\n--- Replaying workflow from {input_file} ---")

        try:
            with Path(input_file).open("r") as f:
                data = json.load(f)
                scenario = Scenario.model_validate(data)
        except Exception as e:  # noqa: BLE001
            print(f"Error loading workflow file: {e}")
            return

        print(f"Workflow: {scenario.name}")
        print(f"Total steps: {len(scenario.steps)}")
        print("-" * 40)

        with WebVisionAgent(headless=headless) as agent:
            for i, step in enumerate(scenario.steps, 1):
                print(f"[{i}/{len(scenario.steps)}] {step.keyword}: {step.text}")

                # Enhanced Deterministic Execution with Verification and Heuristics
                instruction = (
                    f"{step.text}. After performing the action, verify that it was "
                    "successful and the page is in the expected state."
                )

                try:
                    # The enhanced system prompt in WebVisionAgent handles the reasoning loop  # noqa: E501
                    agent.act(instruction)
                except Exception as e:  # noqa: BLE001
                    print(f"Error executing step {i}: {e}")
                    # Heuristic recovery: try to solve common hurdles then retry once
                    print("Attempting heuristic recovery...")
                    try:
                        agent.solve_common_hurdles()
                        agent.act(instruction)
                    except Exception as retry_e:  # noqa: BLE001
                        print(f"Recovery failed: {retry_e}")
                        choice = input("Failed. Continue with next step? (y/n): ")
                        if choice.lower() != "y":
                            print("Replay aborted.")
                            return

        print("-" * 40)
        print("Replay finished successfully.")
