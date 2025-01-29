# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from functools import cached_property
import os

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
        if mask < 0:
            raise ValueError("Mask must be > 0")

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


#
# DFmt (doc format) support
#


class DFmtDoc(Doc):
    """
    Doc parser for the custom doc format.
    """

    def __init__(self, filename: str | os.PathLike):
        """Initialize doc from path."""
        self.filename = filename

        with open(filename, "r") as dump_file:
            #: Raw dump data as plaintext.
            self.raw = dump_file.read()

        self._check_validity()

        super().__init__(
            base_addr=self.header["base_addr"],
            size=self.header["size"]
        )

        self._parse()

    def _check_validity(self):
        """Check if the current doc is valid."""
        if self.header.get("fmt", "unknown") != "doc":
            raise ValueError("\"fmt\" must be set to \"doc\"")
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

    def _parse(self):
        """Parse the loaded doc."""

        # The format is as such:
        #
        # 0x00 NAME
        #   b start_bit end_bit NAME
        #
        # A field can also be given a description by following it with a line
        # starting with an exclamation mark (!).
        #
        # All byte (b) fields following an address field (0x...) are interpreted
        # to be a part of the last found address field.
        #
        # Indentation can be introduced for easier reading, but is ignored by
        # the parser.

        current_addr = None

        header_end = False
        for line in self.raw.split("\n"):
            if line == "--- header_end ---":
                header_end = True
                continue
            if not header_end:
                continue

            line = line.strip()
            if not line:
                continue
            split = line.split()

            # First element is "b": byte
            if split[0] == "b":
                if current_addr is None:
                    raise ValueError("bit data not preceeded by offset")

                current_addr.add_range(DocAddrRange(
                    start_bit=int(split[1]),
                    end_bit=int(split[2]),
                    name=' '.join(split[3:])
                ))

                continue

            # First element is hex address: offset
            try:
                address = int(split[0], 16)
            except ValueError:
                # All other elements are ignored
                continue

            if current_addr:
                self.add_addr(current_addr)

            current_addr = DocAddr(address, name=' '.join(split[1:]))


def doc_to_dfmt(doc: Doc, ftype: str, addr_bits: int = 32, val_bits: int = 32):
    """
    Convert a Doc object to a doc format dump.
    """
    out = "fmt doc\n"
    out += f"type {ftype}\n"
    out += f"base_addr {doc.base_addr}\n"
    out += f"size {doc.size}\n"
    out += f"addr_bits {addr_bits}\n"
    out += f"val_bits {val_bits}\n"
    out += "--- header_end ---\n"

    for addr in sorted(doc.addresses, key=lambda a: a.addr):
        out += f"{hex(addr.addr)} {addr.name}\n"
        for range in sorted(addr.ranges, key=lambda r: r.start_bit):
            out += "\n"
            out += f"  b {range.start_bit} {range.end_bit} {range.name}\n"
        out += "\n"

    return out


def doc_to_dfmt_file(doc: Doc, ftype: str, out_path: str, addr_bits: int = 32, val_bits: int = 32):
    """
    Wrapper for doc_to_dfmt that automatically dumps the doc to a file.
    """
    with open(out_path, "w") as out_file:
        out_file.write(doc_to_dfmt(doc, ftype, addr_bits=addr_bits, val_bits=val_bits))
