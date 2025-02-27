from logbook import Logger

class ControlChangeHandler:
    def __init__(self, logger: Logger, message, templates):
        self.logger = logger
        self.message = message
        self.template_data = templates
        self.result: list[dict[str, any]] = [{}] # Placeholder

        self.logger.debug(f"CC Handler    -> {message}")
