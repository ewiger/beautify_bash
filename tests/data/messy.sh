#!/bin/bash
# A deliberately badly indented script.
set -euo pipefail

greet() {
name="${1:-world}"
if [ -n "$name" ]; then
echo "hello, $name"
else
echo "hello"
fi
}

for i in 1 2 3; do
case "$i" in
1)
greet one
;;
2|3)
greet "many"
;;
*)
echo "done counting"
;;
esac
done

while read -r line; do
echo "$line"
done < /dev/null
