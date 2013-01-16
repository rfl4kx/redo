redo-exec sh -c 'while :; do sleep 10; done' &
echo $! >$3
