"""Ticket #161 item 2 — how long scoring blocks the event loop, measured.

Drives a real uvicorn worker running server.py. Two instruments:

  * **Inside the server**, a task that wants to wake every 5 ms records how far
    it overslept. That is event-loop starvation with no client in the way, and
    it is the number the ADR-0093 trigger should be written against.
  * **Outside**, a keep-alive HTTP client issues /ping at ~50 rps on a raw
    socket (httpx costs more per request than the endpoint does, so it is not
    used here). /ping stands in for sign-in and profile traffic: it does no
    work, so every millisecond it loses is a millisecond the loop was busy.

Scoring load is layered on at 1, 5 and 20 searches per second — §17's range.

Run: python loop_bench.py
"""
from __future__ import annotations

import asyncio
import json
import os
import signal
import statistics
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("BENCH_PORT", "8123"))
HOST = "127.0.0.1"
PING_RPS = 50
DURATION = float(os.environ.get("BENCH_DURATION", "8"))


def pct(xs, p):
    if not xs:
        return float("nan")
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(p / 100.0 * (len(xs) - 1))))]


class Conn:
    """One keep-alive HTTP/1.1 connection, request/response at a time."""

    def __init__(self, reader, writer):
        self.r, self.w = reader, writer

    @classmethod
    async def open(cls):
        r, w = await asyncio.open_connection(HOST, PORT)
        return cls(r, w)

    async def get(self, path):
        self.w.write(f"GET {path} HTTP/1.1\r\nHost: x\r\n\r\n".encode())
        await self.w.drain()
        n = -1
        while True:
            line = await self.r.readline()
            if line.lower().startswith(b"content-length:"):
                n = int(line.split(b":")[1])
            if line in (b"\r\n", b""):
                break
        body = await self.r.readexactly(n) if n > 0 else b""
        return body

    async def close(self):
        self.w.close()
        try:
            await self.w.wait_closed()
        except Exception:
            pass


async def ping_driver(path, rps, duration, out):
    c = await Conn.open()
    interval = 1.0 / rps
    start = time.perf_counter()
    i = 0
    while True:
        due = start + i * interval
        now = time.perf_counter()
        if now - start >= duration:
            break
        if due > now:
            await asyncio.sleep(due - now)
        t0 = time.perf_counter()
        await c.get(path)
        out.append((time.perf_counter() - t0) * 1e3)
        i += 1
    await c.close()


async def load_driver(path, rps, duration, out, conns=8, pool=None):
    pool = pool if pool is not None else [await Conn.open() for _ in range(conns)]
    free = asyncio.Queue()
    for c in pool:
        free.put_nowait(c)
    interval = 1.0 / rps
    start = time.perf_counter()
    i = 0
    tasks = []

    async def one():
        c = await free.get()
        t0 = time.perf_counter()
        try:
            await c.get(path)
            out.append((time.perf_counter() - t0) * 1e3)
        finally:
            free.put_nowait(c)

    while True:
        due = start + i * interval
        now = time.perf_counter()
        if now - start >= duration:
            break
        if due > now:
            await asyncio.sleep(due - now)
        tasks.append(asyncio.create_task(one()))
        i += 1
    await asyncio.gather(*tasks, return_exceptions=True)
    for c in pool:
        await c.close()
    return i


async def run_case(score_path, score_rps, duration=DURATION):
    ctl = await Conn.open()
    await ctl.get("/lag/reset")
    ping_lat, score_lat = [], []
    jobs = [ping_driver("/ping", PING_RPS, duration, ping_lat)]
    if score_path:
        jobs.append(load_driver(score_path, score_rps, duration, score_lat))
    await asyncio.gather(*jobs)
    await ctl.close()
    ctl = await Conn.open()          # fresh: uvicorn closes idle keep-alives
    lag = json.loads(await ctl.get("/lag"))
    await ctl.close()
    return ping_lat, score_lat, lag


async def main():
    rows = os.environ.get("BENCH_ROWS", "31250")
    env = dict(os.environ)
    env["PYTHONPATH"] = HERE
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server:app", "--host", HOST,
         "--port", str(PORT), "--workers", "1", "--log-level", "error",
         "--timeout-keep-alive", "120"],
        cwd=HERE, env=env)
    try:
        for _ in range(180):
            try:
                c = await Conn.open()
                await c.get("/ping")
                await c.close()
                break
            except Exception:
                await asyncio.sleep(1.0)
        else:
            raise SystemExit("server never came up")

        print(f"# loop_bench — CPython {sys.version.split()[0]}, uvicorn 1 worker, "
              f"{rows} rows, /ping at {PING_RPS}/s for {DURATION:.0f}s per case")
        print()

        c = await Conn.open()
        print("| endpoint | single-call ms (median of 15) |")
        print("|---|---|")
        detail = None
        for path in ("/score/inline", "/score/thread",
                     "/score/process_resident", "/score/process_block"):
            ts = []
            for _ in range(15):
                t0 = time.perf_counter()
                body = await c.get(path)
                ts.append((time.perf_counter() - t0) * 1e3)
            print(f"| `{path}` | {statistics.median(ts):.2f} |")
            if path == "/score/process_block":
                detail = json.loads(body)
        await c.close()
        print()
        print(f"process_block detail: {detail}")
        print()

        print("| scoring mode | rps | loop-lag p50 | p99 | p99.9 | max | "
              "ping p50 | ping p99 | ping max | score p50 | score p99 |")
        print("|---|---|---|---|---|---|---|---|---|---|---|")

        def row(name, rps, p, s, lag):
            sp50 = f"{pct(s,50):.1f}" if s else "—"
            sp99 = f"{pct(s,99):.1f}" if s else "—"
            print(f"| {name} | {rps} | {lag['p50']:.2f} | {lag['p99']:.2f} | "
                  f"{lag['p999']:.2f} | {lag['max']:.2f} | {pct(p,50):.2f} | "
                  f"{pct(p,99):.2f} | {max(p):.2f} | {sp50} | {sp99} |")

        p, s, lag = await run_case(None, 0)
        row("none (baseline)", 0, p, s, lag)
        for path in ("/score/inline", "/score/thread",
                     "/score/process_resident", "/score/process_block"):
            for rps in (1, 5, 20):
                p, s, lag = await run_case(path, rps)
                row(f"`{path}`", rps, p, s, lag)
    finally:
        proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    asyncio.run(main())
