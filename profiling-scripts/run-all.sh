#!/bin/bash
#
###############
# Pre-reqs:
###############
# Add @profile decorator in all cloudbridge methods to profile
# `pip install .`
#                in the modified cloudbridge directory (with tests as part of the library)
# `pip install line-profiler`
###############
# Usage:
###############
# sh run-all.sh
###############
# Behavior:
###############
# Will run the line-by-line profiler (https://github.com/rkern/line_profiler) on each test,
# and generate a result file containing the test results and the line-by-line runtime for
# each profiled function

export CB_TEST_PROVIDER=azure

kernprof -l -v run_single.py block_store > ../results/block_store.res
kernprof -l -v run_single.py cloud_factory > ../results/cloud_factory.res
kernprof -l -v run_single.py cloud_helpers > ../results/cloud_helpers.res
kernprof -l -v run_single.py compute > ../results/compute.res
kernprof -l -v run_single.py image > ../results/image.res
kernprof -l -v run_single.py network > ../results/network.res
kernprof -l -v run_single.py object_life_cycle > ../results/object_life_cycle.res
kernprof -l -v run_single.py object_store > ../results/object_store.res
kernprof -l -v run_single.py region > ../results/region.res
kernprof -l -v run_single.py security > ../results/security.res
kernprof -l -v run_single.py vm_types > ../results/vm_types.res
