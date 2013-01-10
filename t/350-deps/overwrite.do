exec >"$3"
. ../skip-if-minimal-do.sh

redo overwrite1 2>&1 && exit 55
REDO_OLD_STDOUT=1 redo overwrite2 2>&1 && exit 56
REDO_OLD_STDOUT=1 redo overwrite3 2>&1 && exit 57
exit 0
