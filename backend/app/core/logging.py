import json
import logging
import sys
from datetime import datetime, timezone

from app.core.config import Environment, Settings


class _JsonFormatter(logging.Formatter):
    """Emits one JSON object per record — ideal for CloudWatch / Loki ingestion.

    Every record carries its environment. Without it a `development` crash and a
    production incident are the same line in the same aggregator, and the difference
    is only recoverable from whichever log stream it happened to arrive on.
    """

    def __init__(self, environment: Environment) -> None:
        super().__init__()
        self._environment = environment

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "env": self._environment,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        for k, v in getattr(record, "extra_fields", {}).items():
            payload[k] = v
        return json.dumps(payload, default=str)


def configure_logging(settings: Settings) -> None:
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    if settings.LOG_JSON:
        handler.setFormatter(_JsonFormatter(settings.APP_ENV))
    else:
        handler.setFormatter(
            logging.Formatter(
                f"%(asctime)s %(levelname)s [{settings.APP_ENV}] %(name)s "
                f":: %(message)s"
            )
        )
    root.addHandler(handler)
    root.setLevel(settings.LOG_LEVEL.upper())
    for name in ("uvicorn.access",):
        logging.getLogger(name).setLevel(logging.WARNING)
