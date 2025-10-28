#!/bin/bash

BASE_ADDR=$1
SIZE=$2

if [ ! $BASE_ADDR ] || [ ! $SIZE ]; then
        echo "usage: $0 <address> <blocksize>"
        exit 1
fi

echo "fmt dump"
echo "type mmio"
echo "base_addr $BASE_ADDR"
echo "size $SIZE"
echo "addr_bits 32"
echo "val_bits 32"
echo "--- header_end ---"

for i in $( seq 0 $(($((SIZE)) / 4)) ); do
        addr=$(($BASE_ADDR + ($i * 4)))
        printf "0x%X " $addr
        val=$(devmem2 $addr l | tail -n1 | cut -d':' -f2)
        case $val in
                *"Memory mapped at address"*) val="-";;
        esac
        echo $val
done
