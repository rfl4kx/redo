if [ -e src ]; then
  redo-ifchange src
  src=$(cat src)
else
  redo-ifcreate src
  src=
fi

echo a$src >$3
echo b$src >$(dirname $3)/b
echo c$src >$(dirname $3)/c
