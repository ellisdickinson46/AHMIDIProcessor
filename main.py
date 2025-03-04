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
from helpers.mdns import ZeroConfService
from helpers.midi import MIDIInterface, MIDIProcessor


class AHMIDIProcessor:
    def __init__(self):
        self.logger = self.initialize_logger()
        self.logger.info("Loading app configuration and templates...")
        self.app_config = AppConfiguration(logger=self.logger)
        self.templates = MessageTemplates(logger=self.logger)
        self.set_logging_parameters()
        self.msg_store = deque(maxlen=15000)

        self.exit_event = threading.Event()
        self.midi_ok = self.setup_midi_communications()
        self.osc_ok = self.setup_osc_client()
        self.mdns_ok = self.setup_service_registration()
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

    def setup_service_registration(self):
        self.logger.info("Registering applicaiton for service discovery...")
        listen_options = self.app_config.osc_options.get("listen")
        self.mdns_service = ZeroConfService(
            app_logger=self.logger,
            svc_port=listen_options.get("svc_port"),
            svc_name=listen_options.get("svc_name"),
            svc_addr=listen_options.get("svc_addr"),
            svc_type=listen_options.get("svc_type"),
            svc_props=listen_options.get("svc_props"),
            svc_ipver=listen_options.get("svc_ipver")
        )
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
            self.midi_in.delete()
        if hasattr(self, "mdns_service"):
            print("exit")
            self.mdns_service.exit_event.set()

    def midi_callback(self, message: tuple, data) -> None:
        msg_bytes, _ = message
        msg_bytes = hexify(msg_bytes)
        self.msg_store.extend(msg_bytes)
        preserve_store = True
        
        # print(self.msg_store)
        
        try:
            if not self.is_complete_midi_message(self.msg_store):
                return
            
            processor = MIDIProcessor(
                self.logger,
                message=self.msg_store,
                data=data,
                templates=self.templates
            )
            preserve_store = False

            self.logger.info(f"Result: {processor.result}")
            if isinstance(processor.result, list):
                for item in processor.result:
                    self.map_to_osc(item)
            else:
                self.logger.error("The handler result attribute must be a list of dictionaries, OSC cannot be sent")
            
            if not preserve_store:
                self.msg_store.clear()
        except Exception:
            self.logger.error("An exception was raised in the callback function.")
            traceback.print_exc()

    def is_complete_midi_message(self, message: deque[str]) -> bool:
        """Determines the expected length of a MIDI message."""
        if not message:
            return None
        if message[0] == "0xf0":
            # print(message[0])
            if message[-1] == "0xf7":
                return True
            return False
        expected_length = self.get_expected_length(message)
        if len(message) == expected_length:
            return True
        return False
    
    def get_expected_length(self, message: deque[str]) -> int | None:
        """Determines the expected length of a MIDI message."""
        if not message:
            return None

        message_type = message[0][2]
        length_info = self.templates.message_types.get(message_type, {}).get("length")
        if isinstance(length_info, int):
            return length_info
        length_info = self.templates.message_types[message_type]["subtype"].get(message[1][2:])
        if isinstance(length_info, int):
            return length_info
        return None
    
    def map_to_osc(self, result) -> None:
        result_type = result.get("result_type", "")
        osc_path_templates = {
            "channel_name": "/qu/channel/{{channel}}/name",
            "channel_fader": "/qu/channel/{{channel}}/fader",
            "channel_pan": "/qu/channel/{{channel}}/pan/{{mix}}",
            "ch_preamp_source": "/qu/channel/{{channel}}/preamp-source",
            "ch_usb_source": "/qu/channel/{{channel}}/usb-source",
            "pafl_select": "/qu/channel/{{channel}}/pafl-select",
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
