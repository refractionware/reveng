#!/bin/bash

I2C_BUS=$1
DEV_ADDR=$2
SIZE=$3

if [ ! $I2C_BUS ] || [ ! $DEV_ADDR ]; then
        echo "usage: $0 <i2cbus> <address> <blocksize>"
        exit 1
fi

[ ! $SIZE ] && SIZE=0xff

echo "fmt dump"
echo "type i2c"
echo "i2c_bus $I2C_BUS"
echo "dev_addr $DEV_ADDR"
echo "base_addr 0x00"
echo "size $SIZE"
echo "addr_bits 8"
echo "val_bits 8"
echo "--- header_end ---"

for addr in $( seq 0 $((SIZE)) ); do
        printf "0x%X " $addr
        val=$(i2cget -fy $I2C_BUS $DEV_ADDR $addr | tail -n1 | cut -d':' -f2)
        case $val in
                *"error"*|*"busy"*) val="-";;
        esac
        echo $val
done
