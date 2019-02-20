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

export CB_TEST_PROVIDER=$1

kernprof -l -v run_single.py block_store > ../results/${CB_TEST_PROVIDER}-block_store.res
kernprof -l -v run_single.py cloud_factory > ../results/${CB_TEST_PROVIDER}-cloud_factory.res
kernprof -l -v run_single.py cloud_helpers > ../results/${CB_TEST_PROVIDER}-cloud_helpers.res
kernprof -l -v run_single.py compute > ../results/${CB_TEST_PROVIDER}-compute.res
kernprof -l -v run_single.py image > ../results/${CB_TEST_PROVIDER}-image.res
kernprof -l -v run_single.py network > ../results/${CB_TEST_PROVIDER}-network.res
kernprof -l -v run_single.py object_life_cycle > ../results/${CB_TEST_PROVIDER}-object_life_cycle.res
kernprof -l -v run_single.py object_store > ../results/${CB_TEST_PROVIDER}-object_store.res
kernprof -l -v run_single.py region > ../results/${CB_TEST_PROVIDER}-region.res
kernprof -l -v run_single.py security > ../results/${CB_TEST_PROVIDER}-security.res
kernprof -l -v run_single.py vm_types > ../results/${CB_TEST_PROVIDER}-vm_types.res
