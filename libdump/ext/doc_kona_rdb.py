# SPDX-License-Identifier: MIT

from ..doc import Doc, DocAddr, DocAddrRange

import os.path


class HeaderParser:
    """
    Turns a header into a dictionary.

    (Note: currently very rudimentary.)
    """

    def __init__(self, path: str, flags: dict[str, str] | None = None):
        if flags:
            raise NotImplementedError(
                "TODO - shell out to a compiler to handle ifdefs"
            )

        with open(path) as header_file:
            self._raw = header_file.read()

        self.data = {}
        for line in self._raw.split("\n"):
            line = line.strip().replace("\t", " ")
            if line.startswith("#define"):
                split = line.split()
                self.data[split[1]] = ' '.join(split[2:])

    def __getitem__(self, index: str):
        return self.data[index]


class KonaRdbDoc(Doc):
    """
    Documentation provider that gathers data from a Broadcom Kona RDB header.
    """

    def __init__(self, base_addr: int, header_path: str):
        header_parsed = HeaderParser(header_path).data

        # RDB files follow the following pattern:
        # #define (blockname)_OFFSET 0x0000....
        # #define (blockname)_TYPE   UInt32
        # #define (blockname)_RESERVED_MASK 0x0000....
        # #define    (blockname)_(varname)_SHIFT 0
        # #define    (blockname)_(varname)_MASK 0x0000.....

        blocks: dict[str, DocAddr] = {}
        current_block = "_none"
        current_offset = 0

        for key, val in header_parsed.items():
            if key.endswith("_OFFSET"):
                current_block = key[:-7]
                current_offset = int(val, 16)
                blocks[current_block] = DocAddr(current_offset, current_block)
            elif key.endswith("_MASK") and not key.endswith("_RESERVED_MASK"):
                if not key.startswith(current_block):
                    raise ValueError(f"Out-of-order line for key {key}")
                range_name = key[len(current_block)+1:-5]
                blocks[current_block].add_range(
                    DocAddrRange.from_mask(int(val, 16), range_name)
                )

        super().__init__(
            name=os.path.splitext(os.path.basename(header_path))[0],
            base_addr=base_addr,
            size=current_offset,
            addresses=list(blocks.values())
        )


def lookup_header_from_sysmap(base_addr: int, sysmap_path: str):
    """
    Get the corresponding header path for the component based on the base
    address and the given sysmap header.
    """

    # brcm_rdb_sysmap.h includes a list of defines for each component's base
    # address, with a comment listing the relevant header file for internal
    # offsets.

    header_parsed = HeaderParser(sysmap_path).data

    for key, val in header_parsed.items():
        if int(val.split("/*")[0].strip(), 16) == base_addr:
            return os.path.join(
                os.path.dirname(sysmap_path),
                val.split("*")[1].strip()
            )

    return None


def gen_dump_commands(sysmap_path: str):
    """
    Get a list of dump commands to run for each address listed in the sysmap.
    """

    # brcm_rdb_sysmap.h includes a list of defines for each component's base
    # address, with a comment listing the relevant header file for internal
    # offsets.

    header_parsed = HeaderParser(sysmap_path).data

    for key, val in header_parsed.items():
        print("#", key)
        addr = int(val.split("/*")[0].strip(), 16)
        rdb = os.path.join(
            os.path.dirname(sysmap_path),
            val.split("*")[1].strip()
        )
        try:
            doc = KonaRdbDoc(addr, rdb)
        except:
            print("# failed to find rdb")
            continue
        print(f"echo ''")
        print(f"echo '!! {key}'")
        print(f"sudo ./devmem-read-block.sh {hex(addr)} {hex(doc.size)}")


    return None
