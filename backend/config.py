import os
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, Any
import dspy


load_dotenv()

class AppConfig:
    API_KEY = os.getenv("OPENAI_API_KEY")
    MODEL_NAME = os.getenv("DSPY_MODEL", "openai/gpt-4o-mini")
    
    TEMP_DIR = Path(os.getenv("TEMP_DIR", "temp"))
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_MB", 2)) * 1024 * 1024 
    MAX_FILE_PAGE = int(os.getenv("MAX_FILE_PAGE", 10)) 
    
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = Path(os.getenv("LOG_FILE", "app.log"))
    
    # Validation threshold
    MIN_CONFIDENCE = 0.6
    
    @classmethod
    def validate(cls):
        """Essential configuration validation"""
        if not cls.API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable must be set")
        cls.TEMP_DIR.mkdir(exist_ok=True, parents=True)

def configure_dspy():
    if not AppConfig.API_KEY:
        raise RuntimeError("OpenAI API key not configured")
    os.environ["OPENAI_API_KEY"] = AppConfig.API_KEY
    lm = dspy.LM(AppConfig.MODEL_NAME)
    dspy.settings.configure(lm=lm)

def get_logging_config() -> Dict[str, Any]:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "colored": {
                "()": "colorlog.ColoredFormatter",
                "format": "%(log_color)s%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "log_colors": {
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red",
                },
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": """
                    asctime: %(asctime)s
                    levelname: %(levelname)s
                    name: %(name)s
                    message: %(message)s
                    pathname: %(pathname)s
                    lineno: %(lineno)d
                """,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "colored",
                "level": AppConfig.LOG_LEVEL,
            },
            "file": {
                "class": "logging.FileHandler",
                "filename": AppConfig.LOG_FILE,
                "formatter": "json",
                "level": "DEBUG",
            },
        },
        "loggers": {
            logger: {
                "handlers": ["console", "file"],
                "level": "WARNING",
                "propagate": False,
            }
            for logger in [
                "LiteLLM",
                "httpx",
                "openai",
                "httpcore",
                "python_multipart",
                "PIL"
            ]
        },
        "root": {
            "handlers": ["console", "file"],
            "level": AppConfig.LOG_LEVEL,
        },
    }

# Initialize configuration on import
try:
    AppConfig.validate()
except ValueError as e:
    raise RuntimeError(f"Invalid configuration: {e}") from e

LOGGING_CONFIG = get_logging_config()