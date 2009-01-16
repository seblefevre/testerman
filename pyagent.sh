#!/bin/sh
export PYTHONPATH=common:core
python pyagent/testerman-agent.py $@ --codec-path=../plugins/codecs/ --probe-path=../plugins/probes/

