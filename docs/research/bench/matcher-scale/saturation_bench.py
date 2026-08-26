"""Ticket #161 item 2, second half — where the knee actually is.

loop_bench.py shows §17's 1-20 searches/second is invisible. This finds the
rate at which it stops being invisible, for two index sizes, so the ADR-0093
trigger-1 threshold can be a number rather than a feeling.

Run: python saturation_bench.py
"""
from __future__ import annotations

import asyncio
import json
import os
import signal
import subprocess
import sys

from loop_bench import Conn, HOST, PORT, load_driver, pct, ping_driver

DURATION = float(os.environ.get("BENCH_DURATION", "6"))
PING_RPS = 50


async def case(path, rps, duration=DURATION):
    # Open every connection *before* resetting the lag histogram, so the
    # accept burst is not counted as scoring's fault.
    pool = [await Conn.open() for _ in range(64)]
    ctl = await Conn.open()
    await ctl.get("/lag/reset")
    await ctl.close()
    ping, score = [], []
    await asyncio.gather(
        ping_driver("/ping", PING_RPS, duration, ping),
        load_driver(path, rps, duration, score, pool=pool))
    ctl = await Conn.open()
    lag = json.loads(await ctl.get("/lag"))
    await ctl.close()
    return ping, score, lag


async def run_for_rows(rows):
    here = os.path.dirname(os.path.abspath(__file__))
    env = dict(os.environ)
    env["PYTHONPATH"] = here
    env["BENCH_ROWS"] = str(rows)
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server:app", "--host", HOST,
         "--port", str(PORT), "--workers", "1", "--log-level", "error",
         "--timeout-keep-alive", "120"],
        cwd=here, env=env)
    try:
        for _ in range(240):
            try:
                c = await Conn.open()
                await c.get("/ping")
                await c.close()
                break
            except Exception:
                await asyncio.sleep(1.0)
        else:
            raise SystemExit("server never came up")

        # unloaded single-call cost, for the utilisation column
        import statistics
        import time
        c = await Conn.open()
        ts = []
        for _ in range(20):
            t0 = time.perf_counter()
            await c.get("/score/inline")
            ts.append((time.perf_counter() - t0) * 1e3)
        await c.close()
        one = statistics.median(ts)

        print(f"\n## {rows:,} rows in the shard, inline scoring "
              f"(unloaded single call: {one:.2f} ms)")
        print("| searches/s | offered util | loop-lag p99 ms | loop-lag max ms | "
              "ping p50 ms | ping p99 ms | ping max ms | search p50 ms | "
              "search p99 ms |")
        print("|---|---|---|---|---|---|---|---|---|")
        for rps in (1, 5, 20, 50, 100, 200, 400):
            ping, score, lag = await case("/score/inline", rps)
            util = f"{rps * one / 1000.0 * 100:.0f}%"
            print(f"| {rps} | {util} | {lag['p99']:.2f} | {lag['max']:.2f} | "
                  f"{pct(ping,50):.2f} | {pct(ping,99):.2f} | {max(ping):.2f} | "
                  f"{pct(score,50):.1f} | {pct(score,99):.1f} |")
    finally:
        proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
        await asyncio.sleep(1.0)


async def main():
    print(f"# saturation_bench — CPython {sys.version.split()[0]}, uvicorn 1 worker, "
          f"/ping at {PING_RPS}/s, {DURATION:.0f}s per point")
    for rows in (31_250, 125_000):
        await run_for_rows(rows)


if __name__ == "__main__":
    asyncio.run(main())
