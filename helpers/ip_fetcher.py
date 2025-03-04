import socket
import psutil

class IPFetcher:
    def __init__(self):
        # Patterns to exclude for IPv4 and IPv6 addresses
        self.exclude_ipv4_patterns = ['127.', '169.254']
        self.exclude_ipv6_patterns = ['::1', 'fe80::']

    def _is_valid_ipv4(self, address):
        """Check if the IPv4 address is valid (not loopback or link-local)."""
        return not any(address.startswith(pattern) for pattern in self.exclude_ipv4_patterns)

    def _is_valid_ipv6(self, address):
        """Check if the IPv6 address is valid (not loopback or link-local)."""
        return not any(address.startswith(pattern) for pattern in self.exclude_ipv6_patterns)

    def get_interface_ips(self):
        """Get all valid IP addresses grouped by interface and type (IPv4, IPv6)."""
        ip_addresses = {}

        # Iterate over all network interfaces
        for interface, addrs in psutil.net_if_addrs().items():
            ip_list = {'ipv4': [], 'ipv6': []}
            
            for addr in addrs:
                match addr.family:
                    # Handle IPv4 addresses (AF_INET)
                    case socket.AF_INET:
                        if self._is_valid_ipv4(addr.address):
                            ip_list['ipv4'].append(addr.address)

                    # Handle IPv6 addresses (AF_INET6)
                    case socket.AF_INET6:
                        if self._is_valid_ipv6(addr.address):
                            ip_list['ipv6'].append(addr.address)

            # Only add interfaces with at least one valid IP address
            if ip_list['ipv4'] or ip_list['ipv6']:
                ip_addresses[interface] = ip_list

        return ip_addresses

    def get_raw_ips(self):
        """
        Get all valid IP addresses (both IPv4 and IPv6) as a flat list,
        ignoring interfaces and IP types.
        """
        ips = self.get_interface_ips()
        raw_ips = []

        # Collect all valid IPs (both IPv4 and IPv6) into a flat list
        for _, addresses in ips.items():
            raw_ips.extend(addresses['ipv4'])
            raw_ips.extend(addresses['ipv6'])

        return raw_ips


# Example Usage
if __name__ == "__main__":
    ip_fetcher = IPFetcher()

    # Get raw IPs
    print("Raw IPs:", ip_fetcher.get_raw_ips())
    print("IPs by interface", ip_fetcher.get_interface_ips())
