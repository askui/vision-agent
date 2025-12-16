CACHE_USE_PROMPT = (
    "<TRAJECTORY USE>\n"
    "    You can use precomputed trajectories to make the execution of the "
    "task more robust and faster!\n"
    "    To do so, first use the RetrieveCachedTestExecutions tool to check "
    "which trajectories are available for you.\n"
    "    The details what each trajectory that is available for you does are "
    "at the end of this prompt.\n"
    "    A trajectory contains all necessary mouse movements, clicks, and "
    "typing actions from a previously successful execution.\n"
    "    If there is a trajectory available for a step you need to take, "
    "always use it!\n"
    "\n"
    "    EXECUTING TRAJECTORIES:\n"
    "    - Use ExecuteCachedTrajectory to execute a cached trajectory\n"
    "    - You will see all screenshots and results from the execution in "
    "the message history\n"
    "    - After execution completes, verify the results are correct\n"
    "    - If execution fails partway, you'll see exactly where it failed "
    "and can decide how to proceed\n"
    "\n"
    "    PLACEHOLDERS:\n"
    "    - Trajectories may contain dynamic placeholders like "
    "{{current_date}} or {{user_name}}\n"
    "    - When executing a trajectory, check if it requires "
    "placeholder values\n"
    "    - Provide placeholder values using the placeholder_values "
    "parameter as a dictionary\n"
    "    - Example: ExecuteCachedTrajectory(trajectory_file='test.json', "
    "placeholder_values={'current_date': '2025-12-11'})\n"
    "    - If required placeholders are missing, execution will fail with "
    "a clear error message\n"
    "\n"
    "    NON-CACHEABLE STEPS:\n"
    "    - Some tools cannot be cached and require your direct execution "
    "(e.g., print_debug, contextual decisions)\n"
    "    - When trajectory execution reaches a non-cacheable step, it will "
    "pause and return control to you\n"
    "    - You'll receive a NEEDS_AGENT status with the current "
    "step index\n"
    "    - Execute the non-cacheable step manually using your "
    "regular tools\n"
    "    - After completing the non-cacheable step, continue the trajectory "
    "using ExecuteCachedTrajectory with start_from_step_index\n"
    "\n"
    "    CONTINUING TRAJECTORIES:\n"
    "    - Use ExecuteCachedTrajectory with start_from_step_index to resume "
    "execution after handling a non-cacheable step\n"
    "    - Provide the same trajectory file and the step index where "
    "execution should continue\n"
    "    - Example: ExecuteCachedTrajectory(trajectory_file='test.json', "
    "start_from_step_index=5, placeholder_values={...})\n"
    "    - The tool will execute remaining steps from that index onwards\n"
    "\n"
    "    FAILURE HANDLING:\n"
    "    - If a trajectory fails during execution, you'll see the error "
    "message and the step where it failed\n"
    "    - Analyze the failure: Was it due to UI changes, timing issues, "
    "or incorrect state?\n"
    "    - Options for handling failures:\n"
    "      1. Execute the remaining steps manually\n"
    "      2. Fix the issue and retry from a specific step using "
    "ExecuteCachedTrajectory with start_from_step_index\n"
    "      3. Report that the cached trajectory is outdated and needs "
    "re-recording\n"
    "\n"
    "    BEST PRACTICES:\n"
    "    - Always verify results after trajectory execution completes\n"
    "    - While trajectories work most of the time, occasionally "
    "execution can be partly incorrect\n"
    "    - Make corrections where necessary after cached execution\n"
    "    - if you need to make any corrections after a trajectory "
    "execution, please mark the cached execution as failed\n"
    "    - If a trajectory consistently fails, it may be invalid and "
    "should be re-recorded\n"
    "    </TRAJECTORY USE>\n"
    "    <TRAJECTORY DETAILS>\n"
    "    There are several trajectories available to you.\n"
    "    Their filename is a unique testID.\n"
    "    If executed using the ExecuteCachedTrajectory tool, a trajectory "
    "will automatically execute all necessary steps for the test with "
    "that id.\n"
    "    </TRAJECTORY DETAILS>\n"
)

PLACEHOLDER_IDENTIFIER_SYSTEM_PROMPT = """You are analyzing UI automation trajectories \
to identify values that should be parameterized as placeholders.

Identify values that are likely to change between executions, such as:
- Dates and timestamps (e.g., "2025-12-11", "10:30 AM", "2025-12-11T14:30:00Z")
- Usernames, emails, names (e.g., "john.doe", "test@example.com", "John Smith")
- Session IDs, tokens, UUIDs, API keys
- Dynamic text that references current state or time-sensitive information
- File paths with user-specific or time-specific components
- Temporary or generated identifiers

DO NOT mark as placeholders:
- UI element coordinates (x, y positions)
- Fixed button labels or static UI text
- Configuration values that don't change (e.g., timeouts, retry counts)
- Generic action names like "click", "type", "scroll"
- Tool names
- Boolean values or common constants

For each placeholder, provide:
1. A descriptive name in snake_case (e.g., "current_date", "user_email")
2. The actual value found in the trajectory
3. A brief description of what it represents

Return your analysis as a JSON object with this structure:
{
  "placeholders": [
    {
      "name": "current_date",
      "value": "2025-12-11",
      "description": "Current date in YYYY-MM-DD format"
    }
  ]
}

If no placeholders are found, return an empty placeholders array."""
