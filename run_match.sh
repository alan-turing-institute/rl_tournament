#!/bin/bash
set -o allexport
source .env
set +o allexport
python3 run_match.py
