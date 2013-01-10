exec >"$3"
echo root $2 ${1#$2} "$(dirname $3)"
