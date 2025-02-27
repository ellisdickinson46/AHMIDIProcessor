import asyncio
import sys
import threading
import traceback
from collections import deque

from jinja2 import Template
from logbook import Logger, StreamHandler
from logbook.more import JinjaFormatter
from helpers.hex import hexify
from helpers.data import AppConfiguration, MessageTemplates
from helpers.osc import OSCClient
from helpers.midi import MIDIInterface, MIDIProcessor


class AHMIDIProcessor:
    def __init__(self):
        self.logger = self.initialize_logger()
        self.logger.info("Loading app configuration and templates...")
        self.app_config = AppConfiguration(logger=self.logger)
        self.templates = MessageTemplates(logger=self.logger)
        self.set_logging_parameters()
        self.msg_store = deque(maxlen=128)

        self.exit_event = threading.Event()
        self.midi_ok = self.setup_midi_communications()
        self.osc_ok = self.setup_osc_client()
        if self.midi_ok and self.osc_ok:
            self.logger.info("Initialization complete, entering ready state. Press Control-C to exit")
            asyncio.run(self.keep_alive())  # Runs the event loop
        else:
            self.logger.error("Initialization failed, cannot enter ready state. Exiting...")
            self.cleanup()

    def initialize_logger(self) -> Logger:
        log_template = """[{{ record.time }}] {{ record.level_name.rjust(8) }} [{{ record.channel }}]: {{ record.message }}"""
        logger = Logger("")
        handler = StreamHandler(
            stream=sys.stdout,
            level="DEBUG"
        )
        formatter = JinjaFormatter(log_template)
        logger.handlers.append(handler)
        handler.formatter = formatter
        return logger

    def set_logging_parameters(self) -> None:
        self.logger.name = self.app_config.app_options.get("application_name", "")
        self.logger.level_name = self.app_config.app_options.get("log_level", "DEBUG")

    def setup_osc_client(self) -> bool:
        self.logger.info("Setting up OSC Communication...")
        self.osc_client = OSCClient(app_logger=self.logger)
        targets = self.app_config.osc_options.get("targets", {}).items()
        for target_name, target_options in targets:
            self.osc_client.add_target(target_name, target_options)
        return True

    def setup_midi_communications(self) -> bool:
        self.logger.info("Setting up MIDI Communication...")
        try:
            self.midi_in = MIDIInterface(
                app_logger=self.logger,
                input_name=self.app_config.midi_options.get("control_port_name"),
                queue_size_limit=self.app_config.midi_options.get("queue_size_limit"),
                sysex_disable=False
            ).midi_instance
            self.midi_in.set_callback(self.midi_callback)
            return True
        except Exception:
            return False

    async def keep_alive(self) -> None:
        try:
            while not self.exit_event.is_set():
                await asyncio.sleep(0.1)  # Prevents blocking execution
        except asyncio.CancelledError:
            print("\b\b", end="")
            self.exit_event.set()
            self.logger.info("Keyboard interrupt received. Exiting...")
        finally:
            self.cleanup()

    def cleanup(self) -> None:
        """Handles cleanup before exiting."""
        self.logger.info("Cleaning up resources...")
        if hasattr(self, "midi_in") and self.midi_in:
            self.midi_in.close_port()

    def midi_callback(self, message: tuple, data) -> None:
        msg_bytes, _ = message
        
        try:
            if len(msg_bytes) > 3:
                # Handle all messages that don't require the queue immediately
                processor = MIDIProcessor(
                    self.logger,
                    message=hexify(msg_bytes),
                    data=data,
                    templates=self.templates
                )
                used_store = False
            else:
                # Handle messages that require the queue only when all bytes are received
                self.msg_store.extend(hexify(msg_bytes))
                if not self.is_complete_midi_message(self.msg_store):
                    return
                
                processor = MIDIProcessor(
                    self.logger,
                    message=self.msg_store,
                    data=data,
                    templates=self.templates
                )
                used_store = True

            self.logger.info(f"Result: {processor.result}")
            if isinstance(processor.result, list):
                for item in processor.result:
                    self.map_to_osc(item)
            else:
                self.logger.error("The handler result attribute must be a list of dictionaries, OSC cannot be sent")
            
            if used_store:
                self.msg_store.clear()
        except Exception:
            self.logger.error("An exception was raised in the callback function.")
            traceback.print_exc()

    def is_complete_midi_message(self, message) -> bool:
        """Determines the expected length of a MIDI message."""
        if not message:
            return None
        expected_length = self.get_expected_length(message)
        if expected_length == 0 or len(message) == expected_length:
            return True
        return False
    
    def get_expected_length(self, message):
        """Determines the expected length of a MIDI message."""
        if not message:
            return None

        message_type = message[0][2]
        length_info = self.templates.message_types.get(message_type, {}).get("length")

        if isinstance(length_info, int):
            return length_info

        return int(self.templates.message_types[message_type]["subtype"].get(message[1][2:], None))
    
    def map_to_osc(self, result):
        result_type = result.get("result_type", "")
        osc_path_templates = {
            "channel_name": "/qu/channel/{{channel}}/name",
            "console_fwversion": "/qu/console/fw-version",
            "console_type": "/qu/console/type",
            "function": "/qu/function/{{function}}",
            "mmc_action": "/qu/mmc/{{action}}"
        }
        if result_type in osc_path_templates:
            template = Template(osc_path_templates[result_type])
            osc_path = template.render(result)
            self.osc_client.send(osc_path, value=result["data"])


if __name__ == "__main__":
    ahmidiprocessor = AHMIDIProcessor()
