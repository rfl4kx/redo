rm -rf b
: > log
redo a/x
[ "$(wc -l <log)" -eq 1 ] || exit 11
cp -a a b
redo b/x
[ "$(wc -l <log)" -eq 2 ] || exit 12
