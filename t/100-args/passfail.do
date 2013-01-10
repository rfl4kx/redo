echo $$ >"$3"
if [ -e pleasefail ]; then
	exit 1
else
	exit 0
fi
