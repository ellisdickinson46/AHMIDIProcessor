"""
JSON File Handler

This module provides a utility function for reading JSON files safely,
handling errors gracefully, and logging relevant information.

Functions:
    read_json(file_name: str, app_logger: Logger, encoding: str = "utf-8") -> Dict[str, Any]
        Reads a JSON file and returns its content as a dictionary.
"""

from typing import Any, Dict
import json
from logbook import Logger


def read_json(file_name: str, app_logger: Logger, encoding: str = "utf-8") -> Dict[str, Any]:
    """Reads a JSON file and returns its content as a dictionary.

    Args:
        file_name (str): The name of the JSON file to read.
        app_logger (Logger): Logger instance for logging messages.
        encoding (str, optional): Encoding format. Defaults to "utf-8".

    Returns:
        Dict[str, Any]: The parsed JSON content.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    try:
        app_logger.debug(f"Attempting to read JSON file: '{file_name}'")
        with open(file_name, "r", encoding=encoding) as json_file:
            data = json.load(json_file)
            app_logger.debug(f"Successfully loaded JSON file: '{file_name}'")
            return data
    except FileNotFoundError as e:
        app_logger.error(f"JSON file not found: {file_name}")
        raise e
    except json.JSONDecodeError as e:
        app_logger.error(f"Invalid JSON format in file '{file_name}': {e}")
        raise e
