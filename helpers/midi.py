import rtmidi

from logbook import Logger
from helpers.hex import hexify
from helpers.sysex import SysExHandler
from helpers.nrpn import NRPNHandler

class MIDIInterface:
    def __init__(self, app_logger: Logger, input_name, queue_size_limit: int = 1024,
                 sysex_disable: bool = False):
        self.logger = app_logger
        self.input_name = input_name
        self.queue_size_limit = queue_size_limit
        self.sysex_disable = sysex_disable

        # Placeholder values
        self.midi_instance = None
        port_index = None

        try:
            self.midi_instance = rtmidi.MidiIn(
                name=input_name,
                queue_size_limit=self.queue_size_limit
            )
            self.midi_instance.ignore_types(sysex=self.sysex_disable)
        except Exception as e:
            self.logger.error(f"Failed to initialize MIDI input: {e}")

        # List available MIDI Ports for debugging
        available_ports = self.midi_instance.get_ports()
        self.logger.debug("Available MIDI ports:")
        for port in available_ports:
            self.logger.debug(f" --> {port}")

        if not available_ports:
            self.logger.error("No available MIDI input ports")
        if self.input_name in available_ports:
            port_index = available_ports.index(input_name)
        else:
            self.logger.error(f"MIDI port '{input_name}' was not found in available ports")

        # Open specified port
        try:
            self.midi_instance.open_port(port_index)
            self.logger.info(f"Opened MIDI port -> '{self.input_name}'")
        except Exception as e:
            self.logger.error(f"Failed to open MIDI port '{self.input_name}': {e}")


class MIDIProcessor:
    def __init__(self, logger: Logger, message: tuple, data, templates):
        self.logger = logger
        self.templates = templates
        self.message = message
        self.data = data
        self.result = [{}]

        self.process()

    def process(self):
        message_type = self.message[0]
        dispatch_map = {
            "0xf0": SysExHandler,
            "0xb": NRPNHandler
        }
        if message_type in dispatch_map:
            self.result = dispatch_map[message_type](
                self.logger,
                list(self.message),
                self.templates
            ).result
        elif message_type[:3] in dispatch_map:
            self.result = dispatch_map[message_type[:3]](
                self.logger,
                list(self.message),
                self.templates
            ).result
        else:
            print("Message Type not implemented yet")
