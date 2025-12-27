import logging
import logging.config
import os
from pathlib import Path


class _LevelFilter(logging.Filter):
    def __init__(self, min_level: int, max_level: int | None = None):
        super().__init__()
        self.min_level = min_level
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        if self.max_level is None:
            return record.levelno >= self.min_level
        return self.min_level <= record.levelno <= self.max_level


def _default_logs_root() -> Path:
    return Path(__file__).resolve().parents[3] / "logs"


def setup_logging(logs_root: Path | None = None) -> None:
    root_logger = logging.getLogger()
    if getattr(root_logger, "_office_automation_configured", False):
        return

    logs_root = logs_root or Path(os.getenv("LOGS_ROOT", _default_logs_root()))
    level_dirs = {
        "debug": logs_root / "debug",
        "info": logs_root / "info",
        "warning": logs_root / "warning",
        "error": logs_root / "error",
    }
    for path in level_dirs.values():
        path.mkdir(parents=True, exist_ok=True)

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "debug_only": {
                "()": _LevelFilter,
                "min_level": logging.DEBUG,
                "max_level": logging.DEBUG,
            },
            "info_only": {
                "()": _LevelFilter,
                "min_level": logging.INFO,
                "max_level": logging.INFO,
            },
            "warning_only": {
                "()": _LevelFilter,
                "min_level": logging.WARNING,
                "max_level": logging.WARNING,
            },
            "error_and_above": {
                "()": _LevelFilter,
                "min_level": logging.ERROR,
            },
        },
        "formatters": {
            "standard": {
                "format": "%(asctime)s %(levelname)s %(name)s: %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "debug_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "standard",
                "filters": ["debug_only"],
                "filename": str(level_dirs["debug"] / "app.log"),
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 3,
                "encoding": "utf-8",
            },
            "info_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "standard",
                "filters": ["info_only"],
                "filename": str(level_dirs["info"] / "app.log"),
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 3,
                "encoding": "utf-8",
            },
            "warning_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "WARNING",
                "formatter": "standard",
                "filters": ["warning_only"],
                "filename": str(level_dirs["warning"] / "app.log"),
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 3,
                "encoding": "utf-8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "standard",
                "filters": ["error_and_above"],
                "filename": str(level_dirs["error"] / "app.log"),
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 3,
                "encoding": "utf-8",
            },
        },
        "root": {
            "level": "DEBUG",
            "handlers": [
                "console",
                "debug_file",
                "info_file",
                "warning_file",
                "error_file",
            ],
        },
    }

    logging.config.dictConfig(logging_config)
    root_logger._office_automation_configured = True
