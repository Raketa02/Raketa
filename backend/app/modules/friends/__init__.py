"""The Friends context — a request between group-mates, and the answer
(``docs/adr/0202`` §1–§2, §8; PRD #743, #745).

**A Friend is someone from your groups whom you asked and who said yes.** One
event-sourced **Friendship** per pair of players, across all their groups: a
request and where it was made, setting it aside (*Not now*), cancelling it, a
crossed request, friends made — by an accept or by the crossing — and a
friendship ended, by a removal or by a block.

**Only the reader's own relations cross.** The reader's relation to a player is
one of *none · sent · asked you · friend* (``domain/relation.py``), lent to the
contexts that draw faces through ports **they** declare, each signed on the
consumer's side of the arrow, so this context imports none of them
(``.importlinter``). A response carries the reader's relations and nobody
else's: Kuba never learns that Tomek and Magda are friends.

**A block ends a friendship**, heard from the outbox, and **a request from a
player the reader blocked is never shown to the reader** — read live from the
reader's own blocks, so the requester still reads *request sent*, exactly as a
request set aside would show them (``docs/adr/0202`` §2).

**Silent everywhere but two places.** A request is told to the person asked,
once, and *friends made* to whoever asked; *Not now*, a cancel, a removal and a
block tell nobody. Notifications hears the events; this context knows nothing
about it.
"""
