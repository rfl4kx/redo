exec >"$3"
redo-ifchange c
echo default-rule
cat c
../sleep 1.4
