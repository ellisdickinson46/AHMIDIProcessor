from logbook import Logger

class SysExHandler:
    def __init__(self, logger: Logger, message, templates):
        self.logger = logger
        self.message = message
        self.template_data = templates
        self.result = {} # Placeholder

        self.action, self.msg_data = self.split_message(self.message)
        self.handle_action(self.action)

    def split_message(self, message):
        sysex_header = self.template_data.sysex_templates["sysex_header"]
        if message[:len(sysex_header)] == sysex_header:
            return [
                message[len(sysex_header):-1][0],
                message[len(sysex_header):-1][1:]
            ]
        return [
            message[1],
            message[2:-1]
        ]


    def handle_action(self, action):
        action_map = {
            "0x02": self.get_channel_name,
            "0x11": self.get_console_info,
            "0x13": self.get_meter_data,
            "0x14": self.handle_end_of_sync,
            "0x7f": self.handle_mmc_action
        }
        if action in action_map:
            action_map[action]()

    def get_console_info(self):
        if len(self.msg_data) == 3:
            box_id, ver_maj, ver_min = self.msg_data
            console_type = self.template_data.console_types.get(box_id, "Unknown")
            self.result =  [
                {
                    "result_type": "console_type",
                    "data": console_type
                },
                {
                    "result_type": "console_fwversion",
                    "data": f"{int(ver_maj, 16)}.{int(ver_min, 16)}"
                }]
        else:
            self.logger.error("Console Information message is malformed.")

    def get_channel_name(self):
        ch_number, ch_name_array = self.msg_data[0], self.msg_data[1:]
        ch_name_str = "".join(bytearray.fromhex(item[2:]).decode() for item in ch_name_array).rstrip('\x00')
        self.result = [{
            "result_type": "channel_name",
            "channel": self.template_data.channel_definitions.get(ch_number, "Unknown"),
            "data": ch_name_str
        }]

    def get_meter_data(self):
        print("Get Meter Data")

    def handle_end_of_sync(self):
        self.result = [{
            "result_type": "function",
            "function": "end-of-sync",
            "data": None
        }]
    
    def handle_mmc_action(self):
        mmc_action = self.msg_data[2]
        self.result = [{
            "result_type": "mmc_action",
            "action": self.template_data.mmc_commands.get(mmc_action, "Unknown"),
            "data": None
        }]
