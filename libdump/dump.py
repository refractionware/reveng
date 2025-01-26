# SPDX-License-Identifier: MIT

from functools import cached_property
import os


class Dump:
    """Class representing dump file."""

    def __init__(self, filename: str | os.PathLike):
        """Initialize dump from path."""
        self.filename = filename

        with open(filename, "r") as dump_file:
            #: Raw dump data as plaintext.
            self.raw = dump_file.read()

        self._check_validity()

    def _check_validity(self):
        """Check if the current dump is valid."""
        if self.header.get("fmt", "unknown") != "dump":
            raise ValueError("\"fmt\" must be set to \"dump\"")
        for key in "type", "base_addr", "size", "addr_bits", "val_bits":
            if key not in self.header:
                raise ValueError(f"missing key \"{key}\"")

    @cached_property
    def header(self) -> dict[str, str]:
        """Header with information about the dump."""
        out = {}
        for line in self.raw.split("\n"):
            if line == "--- header_end ---":
                break
            key, val = line.split(" ")
            out[key] = val
        return out

    @cached_property
    def type(self) -> str:
        """Type of the dump. One of "mmio", "i2c", "unknown"."""
        return self.header.get("type", "unknown")

    @cached_property
    def base_addr(self) -> int:
        """Base address."""
        return int(self.header["base_addr"], 16)

    @cached_property
    def size(self) -> int:
        """Size."""
        try:
            return int(self.header["size"], 16)
        except ValueError:
            return int(self.header["size"])

    @cached_property
    def addr_bits(self) -> int:
        """Amount of bits that the addresses have."""
        return int(self.header["addr_bits"])

    @cached_property
    def val_bits(self) -> int:
        """Amount of bits that the values have."""
        return int(self.header["val_bits"])

    @cached_property
    def data(self) -> dict[int, int]:
        """
        Data contained in the dump.

        Dict with address as the key and dumped value as the value.
        If the address was unreadable, the value is set to -1.
        """
        header_end = False
        out = {}
        for line in self.raw.split("\n"):
            if line == "--- header_end ---":
                header_end = True
                continue
            if header_end is False:
                continue
            try:
                addr_str, val_str = line.split(" ")
            except ValueError:
                continue
            if val_str == "-":
                out[int(addr_str, 16)] = -1
            else:
                out[int(addr_str, 16)] = int(val_str, 16)
        return out
