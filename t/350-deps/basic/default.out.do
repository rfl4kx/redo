redo-ifchange $2.in
exec >"$3"
echo $$
echo $$ >>$2.log
