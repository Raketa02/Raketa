#!/bin/bash
# ---------------------------------------------------------------------------
# The entries of ci.yml's path filters, read as entries. Sourced, never run:
#
#   source "$ROOT/.github/scripts/paths-filter.sh"
#   filter_has "$CI_YML" backend 'backend/**' && ok ... || bad ...
#
# A "still fires" suite proves its gate goes red, and then that the gate is
# REACHED: the filter that decides whether its job runs has to list the files the
# gate reads. Grepping the workflow's text for a path answers a different
# question — whether the path appears anywhere, a comment or another filter's
# entry included — and for months "the backend filter watches the matchmaking
# specs" was green because of the comment explaining why the filter does not use
# that glob (#496).
#
# filter_has <workflow> <filter> <pattern>
#   exit 0  <pattern> is one of <filter>'s entries in the `filters: |` block
#   exit 1  it is not — including when there is no such filter, or no block
#
# It reads what ci.yml's style writes: one filter per `name:` line, one quoted
# entry per `- ` line beneath it, comments on lines of their own or trailing an
# entry. Python rather than a YAML library for the reason check-ci-ok.sh gives:
# the runner's system Python guarantees nothing else.
# ---------------------------------------------------------------------------

filter_has() { # <workflow> <filter> <pattern>
  python3 - "$1" "$2" "$3" <<'PY'
import re, sys
yml, want_filter, want_pattern = sys.argv[1], sys.argv[2], sys.argv[3]
lines = open(yml).read().splitlines()
start = next((i for i, l in enumerate(lines) if l.strip() == "filters: |"), None)
if start is None:
    sys.exit(1)
indent = len(lines[start]) - len(lines[start].lstrip())
block = []
for line in lines[start + 1:]:
    if line.strip() and (len(line) - len(line.lstrip())) <= indent:
        break
    block.append(line)
filters, current = {}, None
for line in block:
    text = re.sub(r"(^|\s)#.*$", "", line).strip()
    key = re.fullmatch(r"([\w-]+):", text)
    if key:
        current = key.group(1)
        filters[current] = []
    elif text.startswith("-") and current:
        filters[current].append(text[1:].strip().strip("'\""))
sys.exit(0 if want_pattern in filters.get(want_filter, []) else 1)
PY
}
