. ../skip-if-minimal-do.sh
rm -rf x y do/log
mkdir -p x/y
redo x/y/z
redo y

[ -e x/y/z -a -e y ] || exit 11
[ $(wc -l <do/log) -eq 2 ] || exit 12

