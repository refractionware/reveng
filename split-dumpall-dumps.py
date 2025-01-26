#!/usr/bin/env python3
# SPDX-License-Identifier: MIT

import argparse
from pathlib import Path
import os

# -- Argument parsing --
argparser = argparse.ArgumentParser(
                    prog='split-dumpall-dumps.py',
                    description='Split the results of dumpall into multiple separate files')
argparser.add_argument("source")
argparser.add_argument("target_dir")
args = argparser.parse_args()
# -- End argument parsing --

source = args.source
target_dir = args.target_dir

Path(target_dir).mkdir(parents=True, exist_ok=True)

with open(source) as source_file:
    data = source_file.read()

cur_out = None
buf = ""
for line in data.split('\n'):
    if line.startswith("!!"):
        if cur_out is not None:
            with open(cur_out, 'w+') as cur_out_file:
                cur_out_file.write(buf)
        buf = ""
        cur_out = os.path.join(target_dir, line.split("!! ")[1].strip() + ".val")
    buf += line + "\n"

if cur_out is not None:
    with open(cur_out, 'w+') as cur_out_file:
        cur_out_file.write(buf)
