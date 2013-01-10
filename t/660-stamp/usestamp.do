exec >"$3"
redo-ifchange stampy
echo $$ >>usestamp.log
cat stampy
