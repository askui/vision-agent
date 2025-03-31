from askui.logger import logger
from askui.settings import settings
from askui.telemetry import Telemetry
from askui.telemetry.processors import Segment


telemetry = Telemetry(settings.telemetry)
telemetry.identify()

if settings.telemetry.segment and settings.telemetry.segment.enabled:
    logger.info("Segment is enabled")
    telemetry.add_processor(Segment(settings.telemetry.segment))
else:
    logger.info("Segment is disabled")
