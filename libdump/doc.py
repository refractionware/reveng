# SPDX-License-Identifier: MIT

from dataclasses import dataclass


@dataclass(slots=True)
class DocAddrRange:
    """Single entry in an address doc; covers a range of bits of the value."""

    #: Start bit, inclusive.
    start_bit: int

    #: End bit, inclusive.
    end_bit: int

    #: Human-readable name.
    name: str

    @classmethod
    def from_mask(cls, mask, name):
        """Create AddrDocEntry from mask. Assumes mask to be continuous."""
        n = 0
        while mask & 1 != 1:
            mask >>= 1
            n += 1
        start_bit = n

        while mask & 1 != 0:
            mask >>= 1
            n += 1
        end_bit = (n - 1)

        return cls(start_bit=start_bit, end_bit=end_bit, name=name)


class DocAddr:
    """
    Documentation provider for a singular address.

    To get an element, access this object with the bit number as the index.
    """

    def __init__(
        self,
        addr: int,
        name: str,
        ranges: list[DocAddrRange] | None = None
    ):
        self.addr = addr
        self.name = name
        if ranges is not None:
            self.ranges = ranges
        else:
            self.ranges = []

    def add_range(self, r: DocAddrRange):
        """Add a range to the doc."""
        if r is None:
            return
        self.ranges.append(r)

    def __getitem__(self, index):
        for r in self.ranges:
            if r.start_bit <= index and r.end_bit >= index:
                return r
        return None

    def __repr__(self):
        return f"<DocAddr {self.name} @ {hex(self.addr)} " \
               f"({len(self.ranges)} ranges)>"


class Doc:
    """
    Documentation provider for a data block.

    To get an element, access this object with the address as the index.
    You can use Doc.base_addr and Doc.size for calculation convenience.
    """

    def __init__(
        self,
        base_addr: int,
        size: int,
        name: str = "",
        addresses: list[DocAddr] | None = None
    ):
        self.base_addr = base_addr
        self.size = size
        self.name = name

        self._indices = {}
        if addresses is not None:
            self.addresses = addresses
            for i in range(len(addresses)):
                self._indices[addresses[i].addr] = i
        else:
            self.addresses = []

    def add_addr(self, addr: DocAddr):
        """Add an address doc to this doc."""
        self.addresses.append(addr)
        self._indices[addr.addr] = len(self.addresses) - 1

    def __getitem__(self, index: int):
        if index in self._indices:
            return self.addresses[self._indices[index]]
        return None

    def __repr__(self):
        return f"<Doc {self.name or 'unnamed'} @ {hex(self.base_addr)} " \
               f"- {hex(self.base_addr + self.size)} " \
               f"(size {hex(self.size)}), " \
               f"{len(self.addresses)} addresses>"
