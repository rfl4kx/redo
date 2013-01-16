rm -f log
echo "fatal should fail" >&2
redo fatal >&/dev/null || true

[ "$(cat log)" = "ok" ] || exit 5
