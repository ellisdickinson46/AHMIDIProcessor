from logbook import Logger

class NRPNHandler:
    def __init__(self, logger: Logger, message, templates):
        self.logger = logger
        self.message = message
        self.template_data = templates
        self.result: list[dict[str, any]] = [{}] # Placeholder
        
        self.logger.debug(f"NRPN Handler  -> {message}")
        self.handle_parameter(self.message[5])

    def handle_parameter(self, parameter) -> None:
        parameter_map = {
            "0x12": self.get_ch_usb_source,
            "0x16": self.get_pan_position,
            "0x17": self.get_fader_position,
            "0x51": self.get_pafl_select,
            "0x57": self.get_ch_preamp_source,
        }
        if parameter in parameter_map:
            parameter_map[parameter]()
    
    def get_fader_position(self):
        ch_number = self.message[2]
        self.result = [{
            "result_type": "channel_fader",
            "channel": self.template_data.channel_definitions.get(ch_number, "Unknown"),
            "data": "placeholder"
        }]

    def get_pan_position(self):
        ch_number = self.message[2]
        pan_position = int(self.message[8], 16) - 37
        self.result = [{
            "result_type": "channel_pan",
            "channel": self.template_data.channel_definitions.get(ch_number, "Unknown"),
            "data": pan_position
        }]
    
    def get_pafl_select(self):
        ch_number = self.message[2]
        pafl_selected = bool(int(self.message[8], 16))
        self.result = [{
            "result_type": "pafl_select",
            "channel": self.template_data.channel_definitions.get(ch_number, "Unknown"),
            "data": pafl_selected
        }]

    def get_ch_preamp_source(self):
        ch_number = self.message[2]
        source_map = {
            "0x00": "local",
            "0x01": "dsnake"
        }
        self.result = [{
            "result_type": "ch_preamp_source",
            "channel": self.template_data.channel_definitions.get(ch_number, "Unknown"),
            "data": source_map.get(self.message[8], "Unknown")
        }]

    def get_ch_usb_source(self):
        ch_number = self.message[2]
        source_map = {
            "0x00": "preamp",
            "0x01": "usb"
        }
        self.result = [{
            "result_type": "ch_usb_source",
            "channel": self.template_data.channel_definitions.get(ch_number, "Unknown"),
            "data": source_map.get(self.message[8], "Unknown")
        }]

