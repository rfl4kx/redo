redo clean

echo "This cause a deadlock, it should fail because of deadlock detection" >&2
redo-ifchange lock1 && exit 11


echo "This used to cause a deadlock. It should neither fail nor lock" >&2
redo-ifchange -j1 a b


