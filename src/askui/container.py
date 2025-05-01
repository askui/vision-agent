from askui.settings import settings
from askui.telemetry import Telemetry
from askui.telemetry.processors import Segment

telemetry = Telemetry(settings.telemetry)

if settings.telemetry.segment:
    telemetry.add_processor(Segment(settings.telemetry.segment))
