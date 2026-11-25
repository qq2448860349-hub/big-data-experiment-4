#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"
java -version
python3 --version
hadoop version
test -x "$SPARK_HOME/bin/spark-submit"
"$SPARK_HOME/bin/spark-submit" --version
processes="$(jps)"
printf '%s\n' "$processes"
for name in NameNode DataNode ResourceManager NodeManager; do
    if ! awk '{print $2}' <<< "$processes" | grep -qx "$name"; then
        echo "Missing $name. Run start-dfs.sh and start-yarn.sh, then retry." >&2
        exit 1
    fi
done
if [[ "$(hdfs getconf -confKey fs.defaultFS)" != hdfs://localhost:9000 ]]; then
    echo 'Check HDFS address in core-site.xml. Expected hdfs://localhost:9000' >&2
    exit 1
fi
hdfs dfs -ls /user/vboxuser
python3 - <<'PY'
import hashlib
import json
from pathlib import Path
data = Path('data/transactions.txt').read_bytes()
manifest = json.loads(Path('data/manifest.json').read_text())
if hashlib.sha256(data).hexdigest() != manifest['sha256']:
    raise SystemExit('Dataset SHA256 mismatch')
print('DATA SHA256 OK:', manifest['sha256'])
PY
echo 'Environment check passed.'
