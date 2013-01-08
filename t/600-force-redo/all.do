redo clean
redo-ifchange mode.sh

. ./mode.sh
[ "$mode" = "$(cat mode)" ] || exit 11

redo mode
redo-ifchange mode.sh

. ./mode.sh
[ "$mode" = "$(cat mode)" ] || exit 12

