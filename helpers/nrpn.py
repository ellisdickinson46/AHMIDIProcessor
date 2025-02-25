from logbook import Logger

class NRPNHandler:
    def __init__(self, logger: Logger, message, templates):
        self.logger = logger
        self.message = message
        self.template_data = templates
        self.result = {} # Placeholder
        print("NRPN Handler", message)
