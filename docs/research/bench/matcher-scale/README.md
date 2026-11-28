# Matcher scale benchmarks

The harness behind [`docs/research/matcher-scale-in-python.md`](../../matcher-scale-in-python.md),
which is the research output for
[`Rakieta02/Rakieta#161`](https://github.com/Rakieta02/Rakieta/issues/161).

**This is throwaway measurement code, not a component.** It lives under `docs/`
deliberately: it is not part of `backend/`, it is not on any import path, it is
not in the Poetry project, and nothing in the product may import from it. Its
only job is that the numbers in the findings file can be re-run and disagreed
with.

**One bench imports the product, and the direction is what makes that safe.**
`candidate_row_bench.py` measures `app.modules.matchmaking.domain.candidate_index`
itself rather than a copy of it, because a copy is exactly what went wrong:
`population.py`'s row is §7.2's *specified* field list, the shipping row diverged
from it before it was ever written, and **782 bytes a row was quoted about the
shipping row from the day the constant was written, having been measured against
the other one** ([#276](https://github.com/Rakieta02/Rakieta/issues/276)). A benchmark whose
subject can drift from the thing it is quoted about measures nothing. The rule
above is unchanged in the direction that matters — the product still may not
import from here — and the module reached for is domain, importing only
`app.kernel` and one value object, both stdlib-only, so the bench still needs
neither the backend's virtualenv nor its dependencies.

## What it measures

| File | Ticket item |
| --- | --- |
| `population.py` | the §7.2 candidate row **as specified**, generated deterministically, in three representations — *not* the row the index holds |
| `scoring.py` | §9.2's scan and §9.3's eight terms, in plain objects and in `array`-packed columns |
| `scoring_numpy.py` | the same eight terms vectorised |
| `native/scan.c` | the same scan in C, so the Python figures have a floor under them |
| `scan_bench.py` | item 1 — cost against row count, four implementations, plus the geo-cell bucket map |
| `terms_bench.py` | item 1 — which of the eight terms the microsecond goes to |
| `doubles_bench.py` | item 6 — C(15,3) x 3, swept over K |
| `memory_bench.py` | item 3 — bytes per row in six shapes, GC pause, refresh headroom — all of §7.2's row |
| `candidate_row_bench.py` | [#276](https://github.com/Rakieta02/Rakieta/issues/276) item 1 — the same measurement against the **shipping** `CandidateRow`, imported |
| `fork_bench.py` | item 3 — whether `--preload` actually shares the index |
| `port_bench.py` | item 7 — the `CandidateSource` port at three granularities; also response serialisation and a query-per-search floor |
| `rebuild_bench.py` | item 5 — projection throughput |
| `lowend_bench.py` | item 8 — in-range candidate counts for a market with tens of players |
| `server.py` | a real FastAPI app with the scoring loop in four places, an event-loop lag monitor and a GC monitor |
| `loop_bench.py` | item 2 — event-loop lag and unrelated-request latency under §17's load |
| `gc_bench.py` | item 3 — what a gen-2 collection does to the p99, with and without `gc.freeze()` |
| `saturation_bench.py` | item 2 — where the knee is |

`results.md` is one captured run, on the hardware named at the top of it.

## Running it

```bash
cd docs/research/bench/matcher-scale
python3.11 -m venv .venv
.venv/bin/pip install fastapi uvicorn numpy orjson psutil
make -C native                      # optional; the C column is skipped without it
PY=.venv/bin/python ./run_all.sh > results.md
```

`numpy` and `psutil` are **not** backend dependencies and must not become ones
on the strength of this. They are installed here only to measure what they
would buy.

`fork_bench.py` needs `os.fork` and so does not run on Windows.
