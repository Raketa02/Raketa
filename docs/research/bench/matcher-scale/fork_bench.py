"""Ticket #161 item 3, the multiplier — is the index really held N times?

`gunicorn --preload` forks workers after the app is imported, so in principle a
pre-built index could be shared copy-on-write. In CPython it usually is not,
because touching an object bumps its refcount and dirties the page. Packed
columns should behave differently: their payload lives in one large buffer that
scanning never writes to.

Measured with USS (unique set size — memory that would be freed if the process
died), which is exactly "how much this worker costs on top of what it shares".

Run: python fork_bench.py       (POSIX only; needs psutil)
"""
from __future__ import annotations

import gc
import os
import sys
import time

import psutil

from population import Columns, Searcher, make_rows
from scoring import SearcherConstants, scan_columns, scan_objects

N = 125_000
WORKERS = 4


def uss(p):
    try:
        return p.memory_full_info().uss
    except Exception:
        return p.memory_info().rss


def child(kind, payload, s, k):
    """Do what a worker does: scan the inherited index, then report USS."""
    for _ in range(5):
        if kind == "objects":
            scan_objects(payload, s, k=k)
        else:
            scan_columns(payload, s, k=k)
    return uss(psutil.Process())


def run(kind, freeze):
    s = Searcher(radius_km=8, mode=0)
    k = SearcherConstants(s)
    rows = make_rows(N)
    payload = rows if kind == "objects" else Columns(rows)
    if kind != "objects":
        del rows
    gc.collect()
    if freeze:
        gc.freeze()
    parent = psutil.Process()
    base_uss = uss(parent)

    rfds = []
    pids = []
    for _ in range(WORKERS):
        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(r)
            try:
                v = child(kind, payload, s, k)
                os.write(w, str(v).encode())
            finally:
                os._exit(0)
        os.close(w)
        rfds.append(r)
        pids.append(pid)

    time.sleep(0.5)
    vals = []
    for r in rfds:
        data = b""
        while True:
            chunk = os.read(r, 4096)
            if not chunk:
                break
            data += chunk
        os.close(r)
        vals.append(int(data))
    for pid in pids:
        os.waitpid(pid, 0)

    per_worker = sum(vals) / len(vals)
    print(f"| {kind} | {'yes' if freeze else 'no'} | {base_uss / 1e6:.0f} | "
          f"{per_worker / 1e6:.0f} | "
          f"{(base_uss + WORKERS * per_worker) / 1e6:.0f} |", flush=True)


def main():
    if not hasattr(os, "fork"):
        print("fork not available on this platform")
        return
    print(f"# fork_bench — CPython {sys.version.split()[0]} on {os.uname().machine}, "
          f"{N:,}-row index, {WORKERS} forked workers each scanning it 5 times")
    print()
    print("| representation | gc.freeze() before fork | parent USS MB | "
          "per-worker USS MB | total MB (parent + 4) |")
    print("|---|---|---|---|---|")
    sys.stdout.flush()
    for kind in ("objects", "packed"):
        for freeze in (False, True):
            pid = os.fork()
            if pid == 0:
                run(kind, freeze)
                sys.stdout.flush()
                os._exit(0)
            os.waitpid(pid, 0)


if __name__ == "__main__":
    main()
