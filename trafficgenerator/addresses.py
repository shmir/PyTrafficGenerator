"""
MAC and IP addresses utilities.
"""
import re

ipv4_re = re.compile(r"([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)")


class MacUtils:
    """MAC utilities.

    todo: replace inside implementation with netaddr?
    """

    def __init__(self, address: str) -> None:
        self.address = address
        try:
            # noinspection PyStatementEffect
            self.standard
        except ValueError as err:
            raise ValueError(f'Invalid MAC format "{address}" - {err}') from err

    def __repr__(self) -> str:
        return self.dotted

    @property
    def standard(self) -> str:
        """Returns MAC address in standard, semicolon, format with leading zeros."""
        if "." in self.address:
            no_dots = self.address.replace(".", "")
            list_of_duos = [a + b for a, b in zip(no_dots[::2], no_dots[1::2])]
            semicolon_format = ":".join(list_of_duos)
        elif "-" in self.address:
            semicolon_format = self.address.replace("-", ":")
        elif ":" in self.address:
            semicolon_format = self.address
        else:
            list_of_duos = [a + b for a, b in zip(self.address[::2], self.address[1::2])]
            semicolon_format = ":".join(list_of_duos)
        if len(semicolon_format.split(":")) != 6:
            raise ValueError(f"MAC should have exactly six literals - {self.address}")
        return ":".join([f"{int(i, 16):02x}" for i in semicolon_format.split(":")]).lower()

    @property
    def no_leading_zeros(self) -> str:
        """Returns MAC address in standard, semicolon, format without leading zeros."""
        return ":".join([f"{int(i, 16):x}" for i in self.standard.split(":")])

    @property
    def hyphened(self) -> str:
        """Returns MAC address in hyphen format (instead of semicolon)."""
        return self.standard.replace(":", "-")

    @property
    def dotted(self) -> str:
        """Returns MAC address in dot format (xxxx.yyyy.zzzz)."""
        no_semicolon = self.standard.replace(":", "")
        quartets = [
            a + b + c + d for a, b, c, d in zip(no_semicolon[::4], no_semicolon[1::4], no_semicolon[2::4], no_semicolon[3::4])
        ]
        return ".".join(quartets)

    @property
    def no_delimiter(self) -> str:
        """Returns MAC address in dot format (xxxxyyyyzzzz)."""
        return self.standard.replace(":", "")


class CnrAddressObject:
    """Base address for CNR MAC/IP addresses."""

    def __init__(self, address: str) -> None:
        self.address = address

    def __repr__(self) -> str:
        return self.address
