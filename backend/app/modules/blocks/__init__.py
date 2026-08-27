"""The Blocks context — the one moderation surface in this build.

``docs/adr/0095`` settles it. A platform whose entire job is putting strangers in
front of each other, with no control that lets somebody say *not them*, has a
safety gap; this is the minimal, real version of that control, and it is
deliberately the **only** one here. A *reason* for a block belongs to a Report,
and reporting is out of scope — so there is no reason field anywhere in this
module and no surface that could grow one.

**The record is directed; the effect is symmetric.** One event-sourced aggregate,
one stream per ordered ``(blocker, blocked)`` pair, so ``A → B`` and ``B → A`` are
two independent streams and one unblock never lifts the other. Neither party is
notified, and no response this module serves carries a block back out.

**It reaches backwards into nothing.** A block removes each from the other's
*future* listings; what it does to a challenge already open is a demand on the
unbuilt ``matches`` context, not a decision this one makes.

The reading half is one port. ``BlockQuery`` answers the searcher's live
exclusion set and the pairwise question, and it **fails closed**: when it cannot
answer it raises, because a query that defaults to *nobody is blocked* is a
safety control that switches itself off under load.
"""
