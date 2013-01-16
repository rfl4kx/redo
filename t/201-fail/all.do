rm -f this-doesnt-exist
echo "this-doesnt-exist is expected to fail" >&2
! redo this-doesnt-exist >&/dev/null || exit 32  # expected to fail
! redo-ifchange this-doesnt-exist >&/dev/null || exit 33  # expected to fail
redo-ifcreate this-doesnt-exist >&/dev/null || exit 34  # expected to pass



rm -f fail ok
echo "fail is expected to fail and ok shouldn't be built" >&2
! redo-ifchange -j1 fail ok >&/dev/null || exit 44  # expected to fail
[ -e ok ] && exit 45 # if fail failed, ok shouldn't be built

touch fail
../flush-cache
REDO_OVERWRITE= redo-ifchange fail >&/dev/null || exit 55  # expected to pass
