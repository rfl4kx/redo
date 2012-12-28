rm -f src
redo a

[ -f a ] && [ a = "$(cat a)" ] || exit 11
[ -f b ] && [ b = "$(cat b)" ] || exit 12
[ -f c ] && [ c = "$(cat c)" ] || exit 13

# Update a dependency
echo 1 > src

redo-ifchange b

[ -f a ] && [ a1 = "$(cat a)" ] || exit 21
[ -f b ] && [ b1 = "$(cat b)" ] || exit 22
[ -f c ] && [ c1 = "$(cat c)" ] || exit 23

# Update a dependency
echo 2 > src

redo-ifchange c

[ -f a ] && [ a2 = "$(cat a)" ] || exit 31
[ -f b ] && [ b2 = "$(cat b)" ] || exit 32
[ -f c ] && [ c2 = "$(cat c)" ] || exit 33

