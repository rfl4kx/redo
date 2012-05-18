#!/usr/bin/env python
import sys, os

import build_context
bc = build_context.init(os.environ, *sys.argv)

import builder, jwack
from log import debug2


def should_build(t):
    return bc.file_from_name(t).should_build(bc.RUNID)


targets = sys.argv[1:]


rv = 202
try:
    if bc.target_name() and not bc.unlocked():
        f = bc.target_file()
        for t in targets:
            f.add_dep('m', t)
        f.save()
        debug2('TARGET: %r\n' % bc.target_full_path())
    else:
        debug2('redo-ifchange: not adding depends.\n')

    try:
        rv = builder.main(bc, targets, should_build)
    finally:
        jwack.force_return_tokens()

except KeyboardInterrupt:
    sys.exit(200)


bc.commit()
sys.exit(rv)
