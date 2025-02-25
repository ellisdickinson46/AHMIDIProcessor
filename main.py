import sys
import threading
import traceback

from jinja2 import Template
from logbook import Logger, StreamHandler
from logbook.more import JinjaFormatter
from helpers.data import AppConfiguration, MessageTemplates
from helpers.osc import OSCClient
from helpers.midi import MIDIInterface, MIDIProcessor


class AHMIDIProcessor:
    def __init__(self):
        self.logger = self.initialize_logger()
        self.app_config = AppConfiguration(logger=self.logger)
        self.templates = MessageTemplates(logger=self.logger)
        self.set_logging_parameters()

        self.exit_event = threading.Event()
        self.midi_ok = self.setup_midi_communications()
        self.osc_ok = self.setup_osc_client()
        if self.midi_ok and self.osc_ok:
            self.logger.info("Initialization complete, entering ready state. Press Control-C to exit")
            self.keep_alive()
        else:
            self.logger.error("Initialization failed, Exiting...")

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
        self.osc_client = OSCClient(app_logger=self.logger)
        targets = self.app_config.osc_options.get("targets", {}).items()
        for target_name, target_options in targets:
            self.osc_client.add_target(target_name, target_options)
        return True

    def setup_midi_communications(self) -> bool:
        try:
            self.midi_in = MIDIInterface(
                app_logger=self.logger,
                input_name=self.app_config.midi_options.get("control_port_name"),
                queue_size_limit=self.app_config.midi_options.get("queue_size_limit")
            ).midi_instance
            self.midi_in.set_callback(self.midi_callback)
            return True
        except Exception:
            return False

    def keep_alive(self) -> None:
        try:
            self.exit_event.wait()
        except KeyboardInterrupt:
            print("\b\b", end="")
            self.exit_event.set()
            self.logger.info("Keyboard interrupt received. Exiting...")
        finally:
            self.midi_in.close_port()

    def midi_callback(self, message, data) -> None:
        try:
            processor = MIDIProcessor(
                self.logger,
                message=message,
                data=data,
                templates=self.templates
            )
            self.logger.info(f"Result: {processor.result}")
            if isinstance(processor.result, list):
                for item in processor.result:
                    self.map_to_osc(item)
            else:
                raise TypeError("The handler result attribute must be a list of dictionaries")
        except Exception:
            self.logger.error("An exception was raised in the callback function.")
            traceback.print_exc()
    
    def map_to_osc(self, result):
        result_type = result["result_type"]
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
    AHMIDIProcessor()
