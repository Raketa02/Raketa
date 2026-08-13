"""The engines layer.

Engines own *computation*, never state. They import only the shared kernel
(``app.kernel``) — never a module (``app.modules.*``), never FastAPI, SQLAlchemy
or any I/O library — and modules import engines freely. The boundary is enforced
by ``import-linter`` in CI (``.importlinter``), not by discipline.

Three purity rules bind every engine (``docs/adr/0015``):

* no clock — ``now`` is an input, never read from the wall clock;
* no randomness — a PRNG is seeded from stable identifiers if one is ever needed;
* no hidden state — a conversational engine takes the whole accumulated transcript.

A shipped engine version is a directory and is never deleted, because a version's
question definitions *are* the code that asked them. The first engine — the
RacketSkill assessment engine — arrives in a later slice.
"""
