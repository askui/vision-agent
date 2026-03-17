import logging
from askui import ComputerAgent
from askui.telemetry.otel import OtelSettings

logging.basicConfig(level=logging.INFO, format="[%(asctime)s.%(msecs)03d] %(levelname)s:%(name)s:%(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

def main() -> None:
    with ComputerAgent(display=1) as agent:
        agent.act(
            goal="Please open a new Chrome window and navegate to askui.com",
            tracing_settings=OtelSettings(enabled=True),
            )

if __name__ == "__main__":
    main()
