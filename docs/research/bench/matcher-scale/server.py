"""Ticket #161 item 2 — a real FastAPI app under a real uvicorn worker.

Four ways to run the scoring loop inside the request path, plus a trivial
endpoint standing in for sign-in and profile traffic. The point of /ping is
that it does no work at all: every millisecond it loses is a millisecond the
event loop was not free.

Started by loop_bench.py; not meant to be run by hand.
"""
from __future__ import annotations

import asyncio
import concurrent.futures as cf
import gc
import multiprocessing as mp
import os
import pickle
import time

from fastapi import FastAPI

from population import Searcher, make_rows
from scoring import SearcherConstants, scan_objects

N_ROWS = int(os.environ.get("BENCH_ROWS", "31250"))

app = FastAPI()
INDEX = None
POOL = None
_SEARCHER = Searcher(radius_km=8, mode=0)

# -- event-loop lag monitor -------------------------------------------------
# A task that wants to wake every 5 ms. Whatever it oversleeps by is time the
# event loop was not free. This is the honest measurement of item 2: it is
# taken inside the process, so no client-side overhead can flatter or spoil it.
LAG_PERIOD = 0.005
LAG: list[float] = []

# -- garbage-collection monitor --------------------------------------------
# A gen-2 collection walks every container object in the process, and the
# candidate index is the biggest pile of them. This records what each pass
# costs and how often it happens, because it lands on the same event loop the
# search does.
GC_EVENTS: list[tuple[int, float]] = []
_gc_t0 = [0.0]


def _gc_cb(phase, info):
    if phase == "start":
        _gc_t0[0] = time.perf_counter()
    else:
        GC_EVENTS.append((info["generation"], time.perf_counter() - _gc_t0[0]))


gc.callbacks.append(_gc_cb)
FREEZE = os.environ.get("BENCH_FREEZE") == "1"


async def _lagmon():
    nxt = time.perf_counter()
    while True:
        nxt += LAG_PERIOD
        d = nxt - time.perf_counter()
        if d > 0:
            await asyncio.sleep(d)
        else:
            await asyncio.sleep(0)
        LAG.append(time.perf_counter() - nxt)


def _worker_init(n):
    global INDEX
    INDEX = make_rows(n)


def _worker_score_resident(_):
    return len(scan_objects(INDEX, _SEARCHER))


def _worker_score_block(payload):
    rows = pickle.loads(payload)
    return len(scan_objects(rows, _SEARCHER))


@app.on_event("startup")
async def _startup():
    global INDEX, POOL
    INDEX = make_rows(N_ROWS)
    if FREEZE:
        gc.collect()
        gc.freeze()
    ctx = mp.get_context("spawn")
    POOL = cf.ProcessPoolExecutor(max_workers=2, mp_context=ctx,
                                  initializer=_worker_init, initargs=(N_ROWS,))
    # pay the spawn + index-build cost before the first request
    list(POOL.map(_worker_score_resident, [0, 0]))
    asyncio.get_running_loop().create_task(_lagmon())


@app.get("/lag/reset")
async def lag_reset():
    LAG.clear()
    GC_EVENTS.clear()
    return {"ok": True}


@app.get("/gc")
async def gc_stats():
    out = {"frozen": gc.get_freeze_count(), "freeze_enabled": FREEZE,
           "counts": list(gc.get_count()), "stats": gc.get_stats()}
    for g in (0, 1, 2):
        ds = sorted(d for gen, d in GC_EVENTS if gen == g)
        out[f"gen{g}"] = {
            "n": len(ds),
            "total_ms": sum(ds) * 1e3,
            "max_ms": (ds[-1] * 1e3) if ds else 0.0,
            "p50_ms": (ds[len(ds) // 2] * 1e3) if ds else 0.0,
        }
    return out


@app.get("/lag")
async def lag():
    xs = sorted(LAG)
    if not xs:
        return {"n": 0}
    def p(q):
        return xs[min(len(xs) - 1, int(round(q / 100.0 * (len(xs) - 1))))] * 1e3
    return {"n": len(xs), "p50": p(50), "p90": p(90), "p99": p(99),
            "p999": p(99.9), "max": xs[-1] * 1e3}


@app.get("/ping")
async def ping():
    return {"ok": True}


@app.get("/score/inline")
async def score_inline():
    n = len(scan_objects(INDEX, _SEARCHER))
    return {"n": n}


@app.get("/score/thread")
def score_thread():
    """A plain `def` endpoint: Starlette runs it in the anyio thread pool."""
    n = len(scan_objects(INDEX, _SEARCHER))
    return {"n": n}


@app.get("/score/process_resident")
async def score_process_resident():
    loop = asyncio.get_running_loop()
    n = await loop.run_in_executor(POOL, _worker_score_resident, 0)
    return {"n": n}


@app.get("/score/process_block")
async def score_process_block():
    """The candidate block has to reach the worker, so it is pickled."""
    k = SearcherConstants(_SEARCHER)
    block = [c for c in INDEX
             if c.sport == k.sport
             and k.lat_lo <= c.area_lat <= k.lat_hi
             and k.lng_lo <= c.area_lng <= k.lng_hi]
    t0 = time.perf_counter()
    payload = pickle.dumps(block, protocol=5)
    t_pickle = time.perf_counter() - t0
    loop = asyncio.get_running_loop()
    n = await loop.run_in_executor(POOL, _worker_score_block, payload)
    return {"n": n, "block": len(block), "pickle_bytes": len(payload),
            "pickle_ms": t_pickle * 1e3}
