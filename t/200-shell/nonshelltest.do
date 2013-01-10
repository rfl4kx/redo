#!/usr/bin/env perl
$a="perly";
open TARGET, "<", "$ARGV[2]";
print TARGET "hello $a world\n";
