---
paths:
  - "tests/demands/**"
  - "app/bootstrap/*_demands.py"
---

# Demand registers (tests/demands/)

Moved verbatim from `backend/CLAUDE.md` (2026-09-30); decisions that are load-bearing and not obvious from the code.

- `tests/demands/` — the **outward demands**, parameterised over every implementation
  registered in a register beside the wiring
  ([ADR-0098](../../../docs/adr/0098-matcher-demands-as-executable-contracts.md)). Adding a row
  to a register enrols an adapter; a port with no row fails the suite. Not named
  *contract* — that word already means `openapi.player.json` drift here.
  **Fourteen registers, and they are fourteen on purpose — one per kind of claim.**
  `app/bootstrap/matcher_demands.py` and `player_record_demands.py` hold the ports a
  *consumer* declares of contexts it does not write; `games_demands.py`,
  `rating_demands.py`, `player_score_demands.py` and `sportsmanship_demands.py` each hold
  the ports one *provider* publishes outward; `challenge_demands.py` holds
  what `challenges` demands of the **matcher** — the arrow's other direction, which
  arrived with the challenge detail read
  ([ADR-0143](../../../docs/adr/0143-the-challenge-is-the-gate-and-the-card-is-recomputed-for-the-reader.md))
  — and `game_demands.py` holds the one thing `games` demands of it, the court's pairing
  ([ADR-0161](../../../docs/adr/0161-the-game-screen-draws-its-courts-pairing.md)), on its own list
  because `games_demands.py` is what that context *publishes* and a demand is the other kind
  of claim;
  `conversation_demands.py` holds what a **room** demands of the three contexts it is
  told by and reads from; and `plan_demands.py` holds what a **plan** demands — the courts
  a player may plan, folded over `challenges` and `games` (ADR-0164 §3), and one fact about
  a *person*. There is deliberately no *conversations provider* and no *plans provider*
  register, and there never will be: a conversation is told and tells nothing, and nothing
  on this side of the wire reads a plan **through a port the Plan declares** — `games` may
  not import it, and the card ladder that reads one is the client's `domain/`. The one fact
  `games` does read off a plan, its agreed moment, is `games`' **own** demand
  (`AgreedMoment`, on `game_demands.py`) that the Plan's adapter signs — the consumer
  contracts its own demand, which is the rule below from the other side (ADR-0162 §4).
  Neither has a consumer of a port it declares, so neither publishes one. **The Plan's court
  read used to be on somebody else's register and no longer is**, and the move is the rule
  rather than an exception to it: while a plan was the game's, *is this player on this
  game's court, and is that game still open to planning* was `games`' question about
  `games`' record, published there as `PlanningCourt` — a consumer contracting its own
  provider's port is the consumer marking its own homework. A plan is the challenge's, the
  question is about a court that may not have become a game yet, and no provider can answer
  it alone; so it is a **demand**, contracted by the consumer that declares it, which is
  `conversation_demands.py`'s shape exactly.
  Each register's exhaustiveness
  assertion is about its own kind of claim and would stop meaning anything with another
  kind in it — which is also the rule for the next one: **a new provider or a new consumer
  gets a new register, not a row in somebody else's**, and the first person to add a row
  should not have to guess which list it belongs in. The sportsmanship register is that
  rule being followed rather than restated: the sportsmanship figure could have been a row
  on the record's consumer list, and a provider's publication on a consumer's register is
  exactly what makes an exhaustiveness assertion a claim about something else. One port on
  the record's list has **three** implementations, which is what the suite has to be
  parameterised over: *where has this reader been shown this person* is a question three
  contexts each answer about themselves.
  **The eleventh, `payments_demands.py`, is a kind of its own**: the two adapters of one port
  onto the outside world — the fake and Stripe — so a fake that drifts from the provider goes red.
  Its rows build over the **settings**, not a session, and one may be absent: Stripe runs only
  where a person placed a test key, and is skipped by name otherwise (ADR-0190 §1).
  **The twelfth, `proposal_demands.py`, is Proposals' consumer register** (#542): Home's and the
  details' three demands — a player's bookings (`bookings`), a booked game's result (`games`), a
  club's distance (the Player profile and `clubs`) — and, since #543, an On request club's
  requests and answers (`bookings`) and the players' Names on them (`users`), and since #544
  what happens to a booked game after the fill (`BookedGameChanges`), a paid share given back
  (`SeatRefunds`) and the card fee on one (`CardFees`) — and since #545 a pool's rescues
  (`PlayerBookings.rescues_in`), a seat taken or declined, and a seat-taken refund. The deck's, the proposer's and the
  fill's ports (#538–#541) were contracted over HTTP only and are owed rows there.
  **The thirteenth, `booking_demands.py`, is Bookings' consumer register** (#543): the first
  free court of a club at an hour with its cut-off and time to confirm, and a club's desk —
  both the Club context's facts — and the Games context's: the ordinary Game a booking opens
  (`GameOpening`, #541, registered by #544) and what leaving, a rescue and the cut-off do
  to it (`GameChanges`, #544, #545).
  **The fourteenth, `bookings_demands.py`, is what Bookings publishes** (#544), beside its
  consumer register as `games_demands.py` stands beside `game_demands.py`: who kept the booked
  games they held a seat on (`BookingHistoryQuery`), *keeps plans*' input.
  **A row carries a builder, and not always over a bare session.** `challenge_demands.py`'s
  takes the two seams the platform supplies from outside a request — the process's
  candidate index and the exposure ledger behind Redis — because the pairing it contracts
  is recomputed through the whole scoring pipeline, and **no test in this repository needs
  Redis running**.
