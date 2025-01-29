# SPDX-License-Identifier: MIT

from ..doc import Doc, DocAddr, DocAddrRange
from ..header_parser import HeaderParser

import os

class BCM59054RegDoc(Doc):
    """
    Parser for include/linux/mfd/bcmpmu59054_reg.h from downstream
    """

    def __init__(self, header_path: str, map: int):
        """
        :param header_path: Path to reg file
        :param map: Which I2C map to document (0 or 1)
        """
        header_parsed = HeaderParser(header_path).data

        blocks: dict[str, DocAddr] = {}
        blocks_nomap: list[str] = []
        current_block = "_none"
        current_offset = 0

        for key, val in header_parsed.items():
            # Offsets use the ENC_PMU_REG(FIFO_MODE, MAPx, offset) macro
            # set in PMU_REG_blockname defines.
            if val.startswith("ENC_PMU_REG"):
                split = [x.strip() for x in val.split(',')]

                if (split[1] == "MAP0" and map != 0) or (split[1] == "MAP1" and map != 1):
                    blocks_nomap.append(key[8:])
                    continue

                current_block = key[8:]
                current_offset = int(split[2][:-1], 16)
                blocks[current_block] = DocAddr(current_offset, current_block)
            elif key.endswith("_MASK"):
                if not key.startswith(current_block):
                    # Out-of-order mask, try to find name
                    block_guess = key.split("_")[0]
                    if block_guess in blocks_nomap:
                        continue
                    if block_guess not in blocks:
                        block_guess = current_block
                    print(f"Out-of-order line for key {key} is assumed to belong to {block_guess}")
                    if block_guess == "_none":
                        continue
                    range_name = key[:-5]
                else:
                    block_guess = current_block
                    range_name = key[len(current_block)+1:-5]

                try:
                    mask = int(val, 16)
                except ValueError:
                    if "<<" in val:
                        # Some masks use the shift and get calculated live
                        split = val.split("<<")
                        width = int(split[0][1:].strip())
                        shift = split[1][:-1]
                        try:
                            shift = int(shift)
                        except ValueError:
                            shift = int(header_parsed[split[1][:-1].strip()])
                        mask = width << shift
                    else:
                        continue

                # Yes, there's a value that has a mask of 0...
                if mask == 0:
                    continue

                blocks[block_guess].add_range(
                    DocAddrRange.from_mask(mask, range_name)
                )

        super().__init__(
            name=os.path.splitext(os.path.basename(header_path))[0],
            base_addr=0x00,
            size=current_offset,
            addresses=list(blocks.values())
        )

