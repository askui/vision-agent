import logging

from sqlalchemy import create_engine

from askui.chat.api.dependencies import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()
connect_args = {"check_same_thread": False}
echo = logger.isEnabledFor(logging.DEBUG)
engine = create_engine(settings.db.url, connect_args=connect_args, echo=echo)
