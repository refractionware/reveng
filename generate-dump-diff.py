#!/usr/bin/env python3
# SPDX-License-Identifier: MIT

import argparse
import datetime
import subprocess
import os.path
from jinja2 import Template
from libdump import Dump
from libdump.ext.doc_kona_rdb import KonaRdbDoc, lookup_header_from_sysmap

RDB_DIR = "/home/knuxify/code/downstream/arch/arm/mach-java/include/mach/rdb/"
SYSMAP_DIR = RDB_DIR + "brcm_rdb_sysmap.h"

# -- Argument parsing --
argparser = argparse.ArgumentParser(
                    prog='generate-dump-diff.py',
                    description='Generate a human-readable diff of two dumps')
argparser.add_argument("foo")
argparser.add_argument("bar")
args = argparser.parse_args()
# -- End argument parsing --

# -- Prepare dumps --
foo = Dump(args.foo)
bar = Dump(args.bar)

val_bits = foo.val_bits

# -- Prepare docs --
doc = None
hdr = lookup_header_from_sysmap(foo.base_addr, SYSMAP_DIR)
if hdr is None:
    print(f"No RDB header found for base address {foo.base_addr}")
else:
    doc = KonaRdbDoc(foo.base_addr, hdr)

# -- Generate HTML table --
with open("_generate_dump_diff_tmpl.html") as template_file:
    TEMPLATE = Template(template_file.read())

now = datetime.datetime.now().strftime("%Y%m%d-%H-%M%-S")

filename = os.path.join("generated-dumps", f"dump_diff_{now}.html")
with open(filename, "w+") as dump_file:
    dump_file.write(TEMPLATE.render(foo=foo, bar=bar, val_bits=val_bits, doc=doc))

subprocess.Popen(["xdg-open", filename])
