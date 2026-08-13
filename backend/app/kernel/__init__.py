"""The shared kernel.

The vocabulary and value objects that every bounded context and every engine
reads verbatim, and that neither may redefine. Nothing here may import a module
(``app.modules.*``), the engines layer, FastAPI, SQLAlchemy or any I/O library —
the kernel is the innermost, dependency-free ring. See
``docs/adr/0015-engines-as-a-pure-versioned-layer.md``.
"""

from app.kernel.sports import SPORT_SPECS, Sport, SportSpec

__all__ = ["SPORT_SPECS", "Sport", "SportSpec"]
