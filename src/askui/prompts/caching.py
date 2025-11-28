CACHE_USE_PROMPT = """<TRAJECTORY USE>
    You can use precomputed trajectories to make the exeuction of the task more robust and faster!
    To do so, first use the RetrieveCachedTestExecutions tool to check which trajectories are available for you.
    The details what each trajectory that is available for you does are at the end of this prompt.
    A trajectory contains all necessary mouse movements, clicks, and typing actions from a previously successful execution.
    If there is a trajectory available for a step you need to take, always use it!
    You can execute a trajectory with the ExecuteCachedExecution tool.
    After a trajectory was executed, make sure to verify the results! While it works most of the time, occasionally,
    the exeuction can be (partly) incorrect. So make sure to verify if everything is filled out as expected,
    and make corrections where necessary!
    </TRAJECTORY USE>
    <TRAJECTORY DETAILS>
    There are several trajectories available to you.
    Their filename is a unique testID.
    If executed using the ExecuteCachedExecution tool, a trajectory will automatically execute all necessary steps for the test with that id.
    </TRAJECTORY DETAILS>
"""
