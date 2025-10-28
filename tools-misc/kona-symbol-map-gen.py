#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Generates a list of symbols from RDB headers that can be imported into Ghidra
(Window -> Script Manager -> ImportSymbolsScript.py).
"""

import os
from libdump.header_parser import HeaderParser
from libdump.ext.doc_kona_rdb import KonaRdbDoc

RDB_DIR = "/home/knuxify/code/android_kernel_samsung_baffinlite/arch/arm/mach-java/include/mach/rdb/"
SYSMAP_DIR = RDB_DIR + "brcm_rdb_sysmap.h"

# Parse sysmap for all base addresses
header_parsed = HeaderParser(SYSMAP_DIR).data

for key, val in header_parsed.items():
    #print("#", key)
    addr = int(val.split("/*")[0].strip(), 16)
    rdb = os.path.join(
        RDB_DIR,
        val.split("*")[1].strip()
    )
    try:
        doc = KonaRdbDoc(addr, rdb)
    except:
        #print("# failed to find rdb")
        continue

    for addr in doc.addresses:
        print(addr.name, hex(doc.base_addr + addr.addr))
