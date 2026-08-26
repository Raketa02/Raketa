"""Ticket #161 item 3, boundary behaviour — what the collector does to the p99.

Same uvicorn worker, same scoring load, run twice: once as CPython leaves it,
once with `gc.freeze()` called after the index is built. Reports how many
gen-2 collections happened, what each cost, and what that did to the loop.

Run: python gc_bench.py
"""
from __future__ import annotations

import asyncio
import json
import os
import signal
import subprocess
import sys

from loop_bench import Conn, HOST, PORT, load_driver, pct, ping_driver

DURATION = float(os.environ.get("BENCH_DURATION", "20"))
PING_RPS = 50
RPS = 20


async def run(freeze: bool, rows: int):
    here = os.path.dirname(os.path.abspath(__file__))
    env = dict(os.environ)
    env["PYTHONPATH"] = here
    env["BENCH_ROWS"] = str(rows)
    env["BENCH_FREEZE"] = "1" if freeze else "0"
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server:app", "--host", HOST,
         "--port", str(PORT), "--workers", "1", "--log-level", "error",
         "--timeout-keep-alive", "300"],
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

        pool = [await Conn.open() for _ in range(16)]
        ctl = await Conn.open()
        await ctl.get("/lag/reset")
        await ctl.close()
        ping, score = [], []
        await asyncio.gather(
            ping_driver("/ping", PING_RPS, DURATION, ping),
            load_driver("/score/inline", RPS, DURATION, score, pool=pool))
        ctl = await Conn.open()
        lag = json.loads(await ctl.get("/lag"))
        g = json.loads(await ctl.get("/gc"))
        await ctl.close()
        return ping, score, lag, g
    finally:
        proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
        await asyncio.sleep(1.0)


async def main():
    rows = int(os.environ.get("BENCH_ROWS_GC", "125000"))
    print(f"# gc_bench — CPython {sys.version.split()[0]}, uvicorn 1 worker, "
          f"{rows:,}-row index, {RPS} searches/s + {PING_RPS} pings/s "
          f"for {DURATION:.0f}s")
    print()
    print("| gc.freeze() | gen2 collections | gen2 total ms | gen2 max ms | "
          "gen1 n | gen1 max ms | loop-lag p99 | loop-lag max | ping p99 | "
          "ping max | search p99 |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for freeze in (False, True):
        p, s, lag, g = await run(freeze, rows)
        print(f"| {'yes' if freeze else 'no'} | {g['gen2']['n']} | "
              f"{g['gen2']['total_ms']:.1f} | {g['gen2']['max_ms']:.1f} | "
              f"{g['gen1']['n']} | {g['gen1']['max_ms']:.1f} | "
              f"{lag['p99']:.2f} | {lag['max']:.2f} | {pct(p,99):.2f} | "
              f"{max(p):.2f} | {pct(s,99):.1f} |")
        print(f"<!-- frozen objects: {g['frozen']}, gen0 n={g['gen0']['n']} "
              f"max={g['gen0']['max_ms']:.2f}ms -->")


if __name__ == "__main__":
    asyncio.run(main())
