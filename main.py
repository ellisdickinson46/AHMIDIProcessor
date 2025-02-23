import time
import sys
from logbook import Logger, StreamHandler
from helpers.json_handler import read_json
from helpers.communicator import open_communication
from helpers.convert import to_padded_hex
from helpers.osc import OSCClient


class AHMIDIProcessor:
    def __init__(self):
        self.hex_message = []

        self.logger = self.setup_logger()
        self.load_configurations()
        self.validate_configurations()
        self.initialize_communication()
        self.idle_loop()

    def idle_loop(self):
        try:
            while True:
                time.sleep(0.05)
        except KeyboardInterrupt:
            print("\b\b", end="")
            self.logger.info("Keyboard interrupt received. Exiting...")
        finally:
            self.midi_in.close_port()

    def setup_logger(self):
        StreamHandler(sys.stdout, level="DEBUG").push_application()
        return Logger("")

    def load_configurations(self):
        """Loads application and template configurations."""
        try:
            self.TEMPLATES = read_json("templates.json", self.logger)
            self.APP_CONFIG = read_json("app_config.json", self.logger)
        except Exception:
            self.logger.error("Error loading configuration files!")
            sys.exit(1)

        self.set_logging_parameters()

    def set_logging_parameters(self):
        """Sets application logging parameters from configuration."""
        try:
            app_options = self.APP_CONFIG.get("app_options", {})
            self.logger.level_name = app_options.get("log_level", "DEBUG")
            self.logger.name = app_options.get("application_name", "")
        except (KeyError, TypeError) as e:
            self.logger.warning(f"Error setting logging parameters: {e}")

    def validate_configurations(self):
        """Ensures that required configurations are properly loaded."""
        if not self.TEMPLATES or not self.APP_CONFIG:
            self.logger.error("Configuration validation failed. Exiting...")
            sys.exit(1)
        self.OSC_OPTIONS = self.APP_CONFIG.get("osc_options", {})

    def initialize_communication(self):
        """Initializes MIDI and OSC communication."""
        self.midi_in = self.setup_midi_communication()
        self.osc_client = self.setup_osc_client()
        self.midi_in.set_callback(self.midi_callback)

    def setup_midi_communication(self):
        midi_options = self.APP_CONFIG.get("midi_options", {})
        return open_communication(
            control_input_name=midi_options.get("control_port_name", ""),
            app_logger=self.logger,
            queue_size_limit=midi_options.get("queue_size_limit", 100)
        )

    def setup_osc_client(self):
        osc_client = OSCClient(app_logger=self.logger)
        for target_name, target_options in self.OSC_OPTIONS.get("targets", {}).items():
            osc_client.add_target(target_name, target_options)
        return osc_client

    def midi_callback(self, message, data=None):
        """Callback function that processes an incoming MIDI message."""
        msg_data, msg_dtime = message
        for item in msg_data:
            self.hex_message.append(to_padded_hex(item))
        if self.is_complete_message(self.hex_message):
            self.process_message(self.hex_message)
            self.hex_message = []

    def is_complete_message(self, message):
        """Checks if a message has reached its expected length."""
        expected_length = self.get_expected_length(message)
        return expected_length is None or len(message) >= expected_length

    def process_message(self, message):
        """Processes an incoming MIDI message."""
        if not message:
            return
        
        dispatch = {
            "0xf0": self.process_sysex_message,
        }
        
        message_type = message[0]
        if message_type in dispatch:
            dispatch[message_type](message)
        elif len(message_type) > 2 and message_type[2] == "b":
            self.process_nrpn_message(message)
        else:
            self.logger.debug(message)

    def get_expected_length(self, message):
        """Determines the expected length of a MIDI message."""
        if not message:
            return None
        
        try:
            message_type = message[0][2]
            length_info = self.TEMPLATES["message_types"].get(message_type, {}).get("length")
            
            if isinstance(length_info, int):
                return length_info
            return int(self.TEMPLATES["message_types"][message_type]["subtype"].get(message[1][2:], None))
        except KeyError:
            return None

    def process_sysex_message(self, message):
        """Handles System Exclusive (SysEx) MIDI messages."""
        sysex_header = self.TEMPLATES.get("sysex_templates", {}).get("sysex_header", [])

        if message[:len(sysex_header)] == sysex_header:
            payload = message[len(sysex_header):-1]
            self.handle_sysex_payload(payload)
        elif len(message) == 6 and message[1] == "0x7f":
            self.handle_mmc_message(message)

    def handle_sysex_payload(self, payload):
        """Processes SysEx payload based on predefined mappings."""
        action_map = {
            "0x11": self.extract_console_info,
            "0x02": self.extract_channel_info,
            "0x14": lambda _: self.logger.info("Received end-of-sync message"),
        }
        
        action = action_map.get(payload[0], self.logger.debug)
        result = action(payload)
        if result:
            self.logger.info(result)

    def extract_console_info(self, data):
        """Extracts console information from SysEx data."""
        box_id, ver_maj, ver_min = data[1:]
        console_type = self.TEMPLATES["console_types"].get(box_id, "unknown")
        return {"type": console_type, "firmware": f"{int(ver_maj, 16)}.{int(ver_min, 16)}"}

    def extract_channel_info(self, data):
        """Extracts channel information from SysEx data."""
        ch_number, ch_name_array = data[1], data[2:]
        ch_name_str = "".join(bytearray.fromhex(item[2:]).decode() for item in ch_name_array).rstrip('\x00')
        return f"{self.TEMPLATES['channel_definitions'].get(ch_number, 'Unknown')}, Name: '{ch_name_str}'"

    def handle_mmc_message(self, data):
        """Processes MMC (MIDI Machine Control) messages."""
        action = data[4]
        action_type = self.TEMPLATES["mmc_commands"].get(action, "Unknown MMC Command")
        self.logger.info(f"MMC message received: {action_type}")
        self.osc_client.send(f"/{action_type}")

    def process_nrpn_message(self, message):
        """Handles NRPN MIDI messages."""
        self.logger.debug(message)


if __name__ == "__main__":
    AHMIDIProcessor()
