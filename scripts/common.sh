#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
export HADOOP_HOME=/home/vboxuser/hadoop
export HADOOP_CONF_DIR="$HADOOP_HOME/etc/hadoop"
export SPARK_HOME="${SPARK_HOME:-/home/vboxuser/spark-3.5.8-bin-hadoop3}"
export PATH="$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PATH"
export PYSPARK_PYTHON=/usr/bin/python3
export PYSPARK_DRIVER_PYTHON=/usr/bin/python3
