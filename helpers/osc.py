from concurrent.futures import ThreadPoolExecutor
from logbook import Logger
from pythonosc import udp_client


class OSCClient:
    """A high-performance client for managing and sending OSC messages to multiple targets."""

    def __init__(self, app_logger: Logger):
        """Initialize an OSC client with logging support.

        Args:
            app_logger (Logger): Logger instance for debugging and error reporting.
        """
        self.app_logger = app_logger
        self.targets: dict[str, udp_client.SimpleUDPClient] = {}
        self.executor = ThreadPoolExecutor(max_workers=5)  # Limit to 5 concurrent threads

    def add_target(self, target_name: str, target_options: dict[str, any]):
        """Register a new OSC target with its address and port.

        Args:
            target_name (str): The name identifier of the OSC target.
            target_options (dict[str, any]): A dictionary containing:
                - "address" (str): IP address or hostname of the OSC target.
                - "port" (int): Port number to send messages to.

        Raises:
            ValueError: If target_options are missing required keys or have invalid types.
        """
        address = target_options.get("address")
        port = target_options.get("port")

        if not isinstance(address, str) or not isinstance(port, int):
            raise ValueError(f"Invalid address '{address}' or port '{port}' for target '{target_name}'.")

        if target_name in self.targets:
            self.app_logger.warning(f"Target '{target_name}' is already registered. Overwriting.")

        self.targets[target_name] = udp_client.SimpleUDPClient(address, port)
        self.app_logger.debug(f"Added OSC target '{target_name}' ({address}:{port}).")

    def send(self, path: str, value: any = None):
        """Send an OSC message to all registered targets in parallel.

        Args:
            path (str): The OSC address pattern (must start with '/').
            value (any, optional): The value to send with the message. Defaults to None.

        Raises:
            ValueError: If the OSC path is invalid.
        """

        if not isinstance(path, str) or not path.startswith("/"):
            raise ValueError(f"Invalid OSC path: '{path}'. Must be a string starting with '/'.")

        if not self.targets:
            self.app_logger.warning("No OSC targets registered. Message not sent.")
            return

        def send_message(target_name: str, client: udp_client.SimpleUDPClient):
            """Send message to a specific target."""
            try:
                client.send_message(path, value)
                self.app_logger.debug(f"Sent to '{target_name}' - Path: {path}, Value: {value}")
            except Exception as e:
                self.app_logger.error(f"Error sending to '{target_name}': {e}")

        futures = [self.executor.submit(send_message, name, client) for name, client in self.targets.items()]
        
        for future in futures:
            future.result()  # Ensures all messages are sent before returning
