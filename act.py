from askui import VisionAgent

with VisionAgent(log_level="DEBUG") as agent:
    agent.act("Click on the 'X' button to cancel the current search in Google Maps")
    agent.act(
        "Search for 'Linienstraße 145' in Google maps to find the route there from 'Google Berlin'"
    )
