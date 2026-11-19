#!/bin/sh
# Regression check for construct chains and possessives: ./tests/run.sh
# tests/constructs.hbo.txt is hand-made (apertium-hbo tags, made-up ids 9000…), for the
# patterns Gen 1 lacks (nested person chains, adjective agreement, suffix + adjective/numeral), and inferred quotation marks with their overrides.
cd "$(dirname "$0")/.."
CONSTRUCTS=tests/constructs.tsv PRONOUNS=tests/pronouns.tsv PUNCTUATION=tests/punctuation.tsv ./translate.sh tests/constructs.hbo.txt 2>/dev/null \
    | diff -u tests/constructs.expected - && echo "constructs: ok"
