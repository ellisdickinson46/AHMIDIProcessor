"""
JSON File Handler

This module provides a utility function for reading JSON files safely,
handling errors gracefully, and logging relevant information.

Functions:
    read_json(file_name: str, app_logger: Logger, encoding: str = "utf-8") -> Dict[str, Any]
        Reads a JSON file and returns its content as a dictionary.
"""
import asyncio
import json

import aiofiles
from logbook import Logger


class JSONHandler:
    def __init__(self, logger: Logger, json_file=None, encoding="utf-8"):
        self.logger = logger
        self.file_name = json_file
        self.encoding = encoding
        self.json_data = asyncio.run(self.read_json())

    async def read_json(self) -> dict[str, any]:
        self.logger.debug(f"Attempting to read JSON file: '{self.file_name}'")
        try:
            async with aiofiles.open(self.file_name, "r", encoding=self.encoding) as json_file:
                data = await json_file.read()
                return json.loads(data)
        except FileNotFoundError as e:
            self.logger.error(f"JSON file not found: {self.file_name}")
            raise e
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON format in file '{self.file_name}': {e}")
            raise e
