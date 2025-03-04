from logbook import Logger
from helpers.json import JSONHandler


class AppConfiguration:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.raw_data = JSONHandler(
            logger=self.logger,
            json_file="app_config.json"
        ).json_data

        self.app_options = self.raw_data["app_options"]
        self.midi_options = self.raw_data["midi_options"]
        self.osc_options = self.raw_data["osc_options"]
    
    def validate_config(self) -> None:
        # Not yet implemented
        pass


class MessageTemplates:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.raw_data = JSONHandler(
            logger=self.logger,
            json_file="templates.json"
        ).json_data

        self.message_types = self.raw_data["message_types"]
        self.sysex_templates = self.raw_data["sysex_templates"]
        self.console_types = self.raw_data["console_types"]
        self.mmc_commands = self.raw_data["mmc_commands"]
        self.channel_definitions = self.raw_data["channel_definitions"]
        self.mix_pan_definitions = self.raw_data["mix_pan_definitions"]
