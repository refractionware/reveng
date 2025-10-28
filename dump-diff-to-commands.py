#!/usr/bin/env python3
from libdump.dump import Dump

import argparse
from libdump import Dump

RDB_DIR = "/home/knuxify/code/downstream/arch/arm/mach-java/include/mach/rdb/"
SYSMAP_DIR = RDB_DIR + "brcm_rdb_sysmap.h"

# -- Argument parsing --
argparser = argparse.ArgumentParser(
                    prog='generate-dump-diff.py',
                    description='Generate commands for dumping diffed values')
argparser.add_argument("foo", help="Dump of current state")
argparser.add_argument("bar", help="Dump to replace the current state")
args = argparser.parse_args()
# -- End argument parsing --

# -- Prepare dumps --
foo = Dump(args.foo)
bar = Dump(args.bar)

# -- Do a diff --
diff = {}
for addr, val in foo.data.items():
    if val != bar.data[addr]:
        diff[addr] = bar.data[addr]

base_addr = foo.base_addr

# -- Format the diff into commands --
if foo.type == "i2c":
    for addr, val in diff.items():
        print(f"sudo i2cset -f -y 0 0xFIXME {hex(addr)} {hex(val)}")
elif foo.type == "mmio":
    if foo.val_bits == 32:
        devmem_mode = "w"
    elif foo.val_bits == 16:
        devmem_mode = "h"
    elif foo.val_bits == 8:
        devmem_mode = "b"
    for addr, val in diff.items():
        print(f"sudo devmem2 {hex(addr)} {devmem_mode} {hex(val)}")
