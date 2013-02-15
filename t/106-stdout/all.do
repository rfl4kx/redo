unset REDO_OLD_STDOUT
unset REDO_WARN_STDOUT
[ "$(redo stdout)" == toto ] || exit 11

export REDO_OLD_STDOUT=1
[ "$(redo stdout)" == "" ] || exit 21
[ "$(cat stdout)" == "toto" ] || exit 22

unset REDO_OLD_STDOUT
export REDO_WARN_STDOUT=1
if val="$(redo stdout)"; then
  exit 31 # Should fail if --warn-stdout
fi

export REDO_OLD_STDOUT=1
if ! val="$(redo stdout)"; then
  exit 41
elif [ "$val" != "" ]; then
  exit 42
elif [ "$(cat stdout)" != "toto" ]; then
  exit 43
fi

