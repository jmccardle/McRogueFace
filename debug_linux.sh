#!/bin/bash
cp src/scripts/*.py bin/linux/scripts/
cd bin/linux
gdb ./mcrogueface
