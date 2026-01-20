CACHE_USE_PROMPT = (
  "<TRAJECTORY_USE>\n"
  "CRITICAL: Before taking ANY action, you MUST first call the"
  " retrieve_available_trajectories_tool to check for cached trajectories. If the"
  " name of an available cached trajectory matches the one specified by the user,"
  " you MUST execute it using the execute_cached_executions_tool before calling any"
  " other tools!\n"
  "\n"
  "WORKFLOW:\n"
  "1. ALWAYS start by calling retrieve_available_trajectories_tool\n"
  "2. If a matching cached trajectory exists, execute it immediately using"
  " the execute_cached_executions_tool"
  "3. Only proceed with manual execution if no matching trajectory is available\n"
  "\n"
  "EXECUTING TRAJECTORIES:\n"
  "- Use execute_cached_executions_tool to run cached trajectories\n"
  "- Trajectories contain complete sequences of mouse movements, clicks, and typing"
  " from successful executions\n"
  "- You'll see all screenshots and results in message history\n"
  "- Verify results after execution completes\n"
  "\n"
  "DYNAMIC PARAMETERS:\n"
  "- Trajectories may require parameters like {{current_date}} or {{user_name}}\n"
  "- Provide values via parameter_values as a dictionary\n"
  "- Example: execute_cached_executions_tool(trajectory_file='test.json',"
  " parameter_values={'current_date': '2025-12-11'})\n"
  "- Missing required parameters will cause execution failure with an error message."
  " In that case try again with providing the correct parameters\n"
  "\n"
  "NON-CACHEABLE STEPS:\n"
  "- Some steps cannot be cached (e.g., print_debug, contextual decisions)\n"
  "- Trajectory pauses at non-cacheable steps, returning NEEDS_AGENT status with"
  " current step index\n"
  "- Execute the non-cacheable step manually\n"
  "- Resume using execute_cached_executions_tool with start_from_step_index"
  " parameter\n"
  "\n"
  "CONTINUING TRAJECTORIES:\n"
  "- Resume after non-cacheable steps:"
  " execute_cached_executions_tool(trajectory_file='test.json',"
  " start_from_step_index=5, parameter_values={...})\n"
  "\n"
  "FAILURE HANDLING:\n"
  "- On failure, you'll see the error and failed step index\n"
  "- Options: (1) Execute remaining steps manually, (2) Retry from specific step"
  " using start_from_step_index, (3) Report trajectory as outdated\n"
  "- Mark failing trajectories as invalid after the execution\n"
  "\n"
  "BEST PRACTICES:\n"
  "- Always verify results after execution\n"
  "- Trajectories occasionally execute incorrectly - make corrections as needed\n"
  "- Mark executions as failed if corrections are required\n"
  "- Trajectory filenames are unique test IDs that automatically execute all steps"
  " for that test\n"
  "</TRAJECTORY_USE>\n"
)

CACHING_PARAMETER_IDENTIFIER_SYSTEM_PROMPT = """You are analyzing UI automation \
trajectories to identify values that should be parameterized as parameters.

Identify values that are likely to change between executions, such as:
- Dates and timestamps (e.g., "2025-12-11", "10:30 AM", "2025-12-11T14:30:00Z")
- Usernames, emails, names (e.g., "john.doe", "test@example.com", "John Smith")
- Session IDs, tokens, UUIDs, API keys
- Dynamic text that references current state or time-sensitive information
- File paths with user-specific or time-specific components
- Temporary or generated identifiers

DO NOT mark as parameters:
- UI element coordinates (x, y positions)
- Fixed button labels or static UI text
- Configuration values that don't change (e.g., timeouts, retry counts)
- Generic action names like "click", "type", "scroll"
- Tool names
- Boolean values or common constants

For each parameter, provide:
1. A descriptive name in snake_case (e.g., "current_date", "user_email")
2. The actual value found in the trajectory
3. A brief description of what it represents

Return your analysis as a JSON object with this structure:
{
  "parameters": [
    {
      "name": "current_date",
      "value": "2025-12-11",
      "description": "Current date in YYYY-MM-DD format"
    }
  ]
}

If no parameters are found, return an empty parameters array."""
