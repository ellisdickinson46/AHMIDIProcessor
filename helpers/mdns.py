import asyncio
import threading

from logbook import Logger
from zeroconf import IPVersion, ServiceInfo, Zeroconf
from helpers.ip_fetcher import IPFetcher


class ZeroConfService:
    def __init__(self, app_logger: Logger, svc_port, svc_name, svc_addr, svc_type, svc_props, svc_ipver) -> None:
        """Initialize the Zero-configuration Service
        
        Args:
            app_logger (Logger): A logger instance for logging service events
            svc_port      (int): Port Number that OSC should listen on
            svc_name      (str): Advertised name of the Zeroconf Service
            svc_addr      (str): Domain name for the Zeroconf Service
            svc_type      (str): Zeroconf Service Type
            svc_props    (dict): Zeroconf Service Properties
            svc_ipver     (str): IP Version to use for the Zeroconf Service
        """
        self.logger = app_logger
        self.ip_addresses = IPFetcher().get_raw_ips()

        self.svc_port = svc_port
        self.svc_name = svc_name
        self.svc_addr = svc_addr
        self.svc_type = svc_type
        self.svc_props = svc_props
        self.svc_ipver = self.get_ip_ver(svc_ipver)

        if self.svc_ipver is None:
            raise ValueError(f"Invalid IP version: {self.svc_ipver}")

        self.zeroconf = Zeroconf(ip_version=self.svc_ipver)
        self.register_service()

        self.exit_event = threading.Event()
        self.thread = threading.Thread(target=self.run_service_worker, daemon=True)
        self.thread.start()

    def get_ip_ver(self, ip_ver) -> IPVersion | None:
        """Convert a string IP Version into an IPVersion enum
        
        Args:
            ip_ver (str): IP Version
        Returns:
            IPVersion | None: Corresponding IPVersion enum value, or None if invalid
        """
        match ip_ver:
            case "v4":
                return IPVersion.V4Only
            case "v6":
                return IPVersion.V6Only
            case "all":
                return IPVersion.All
            case _:
                return None

    def run_service_worker(self) -> None:
        """Run the service worker in an asyncio event loop in a separate thread"""
        asyncio.run(self.service_worker())

    async def service_worker(self) -> None:
        """Async service worker that registers the service and keeps it alive"""
        try:
            while not self.exit_event.is_set():
                await asyncio.sleep(0.1)
        finally:
            self.unregister_service()

    def register_service(self) -> None:
        """Register the Zeroconf service with defined attributes"""
        self.logger.debug("Registering zeroconf service...")
        self.svc_info = ServiceInfo(
            self.svc_type,
            f"{self.svc_name}.{self.svc_type}",
            addresses=self.ip_addresses,
            port=self.svc_port,
            properties=self.svc_props,
            server=self.svc_addr,
        )
        self.zeroconf.register_service(self.svc_info)

    def unregister_service(self) -> None:
        """Unregister and close the Zeroconf service"""
        self.logger.debug("Unregistering zeroconf service...")
        self.zeroconf.unregister_service(self.svc_info)
        self.zeroconf.close()
