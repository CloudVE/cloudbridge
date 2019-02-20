#!/bin/bash

sh run-provider.sh aws
sh run-provider.sh azure
sh run-provider.sh gcp
sh run-provider.sh openstack

python filter-summarize.py
