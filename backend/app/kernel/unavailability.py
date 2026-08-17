"""The closed set of reasons the kernel itself can give.

Its own module, and not part of ``results.py``, because the union is assembled
*from* the modules that produce its members: ``results.py`` owns the machinery
(``Ok``, ``Err``, the ``Reason`` protocol) and knows nothing about time or
money, while this file knows every reason and no machinery. Written the other
way round the two would import each other.

So this is the one page to read to learn everything the kernel can refuse, and
adding a member is a one-line diff on it. ``exhaustive`` then fails the build at
every ``match`` that does not handle the new member, which is the whole reason
the set is written down rather than left implicit in the return types.

It **shipped empty**, spelled ``Never``, until the time module landed the
nonexistent-local-time case (``docs/adr/0024``); a reason invented ahead of its
producer is a guess about a domain question this repo has left open.
"""

from __future__ import annotations

from typing import TypeAlias

from app.kernel.time import NonexistentLocalTime

#: Every reason the kernel can give for having no answer.
Unavailable: TypeAlias = NonexistentLocalTime
