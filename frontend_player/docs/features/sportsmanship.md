# sportsmanship — the star card

> The design record for `src/features/sportsmanship/` — what the feature does and the reasons the shape
> is what it is, one paragraph per decision. Moved out of `CLAUDE.md` on 2026-09-11 so it loads
> when this feature is being changed rather than on every turn. **Append here** when a ticket
> changes what this feature does. Index: [`README.md`](README.md).

**A card at the end of the game screen asks how the other players were, and it is
`features/sportsmanship/`**
([#386](https://github.com/Raketa02/Raketa/issues/386),
[ADR-0158](../../../docs/adr/0158-a-rating-is-one-per-person-and-the-collapse-is-the-key.md)). **The
word _rating_ is Skill rating's**, so everything in the feature is spelled **stars** or **the
card**: a bare _rating_ on this platform is still the μ/σ a player holds in a sport, and these
two things now stand one section apart on the same tab. A card carries **everybody else who was
on that court** — in doubles both opponents _and your partner_, because the person who saw you
play closest was on your own side of the net — each taking one to five whole stars, and there
is no _side_ anywhere on it. **Two of the ticket's rules are unrepresentable rather than
validated**: the scale is a five-member union, so `stars_are_one_to_five` cannot be earned, and
a draft keyed by player id cannot hold two answers about one person, which is a refusal the
backend spells out rather than collapsing. The third is the blank — **an absence and nothing
else**, not a zero and not a null — which is why the row's value is optional and why `starsGiven`
reads the draft **through the card's own list**, so stars for somebody who was not there are
never assembled.

**The window is the server's and this side never re-derives it.** A card appears the day after
the game and stays seven days; one not yet a day old, one whose week has run out and one already
answered are all simply **not on the list**, and _none of them is something to draw differently_.
So the section draws exactly what it was handed — a second spelling of that window here would
eventually disagree with the one the `POST` is judged against, and it would disagree silently.
**The route answers ids and nothing else**, deliberately, so the words come from the game the
card is drawn on: `GameScreen` composes `StarCardSection` under everything else on the page
and hands down the one court it already holds. `RatedCourt` is declared in `sportsmanship` and
satisfied structurally by `Game`, which is the seam the builder has with the challenge send —
**the surface composes and the feature owns the act** — and a court the server did not name
draws nothing rather than a card with ids in it.

**It is at the foot of the game screen rather than above the games list, and the trade is
stated rather than discovered.** A card is a question about one evening, and the moment anybody
is thinking about how an evening went is the moment they are looking at what came of it — which
is that screen and not a row. What it costs is that **nothing surfaces the card**: Now no longer
mentions one, so a player who never re-opens a settled game never sees it, and because both
gates are the server's the card is not there at the moment a score is entered either — it
appears the next time that game is opened, settled and a day old. Both are affordable only
because ignoring a card costs nothing and always did, which is the same ground the next
paragraph but one stands on.

**Everything the press cannot be taken back from is said before it.** The contract's own
instruction is _"there is no correction path — so ask before you send"_, and the card asks by
**stating**: what a star does — _it won't stop you being matched with them_, above the rows
rather than beside the button, because a player decides what a star means while they are
tapping and **Pass and Block already exist and both mean something specific** — that anybody
may be left blank, and that sending closes the card for good. A pre-send sheet was weighed and
refused: `ProposeSheet` exists because a challenge reaches four other people and starts a
window nobody can stop, where this reaches nobody and tells nobody. What stands in its place is
a row that **clears when the star already standing is pressed again**, which is the one gesture
that makes a mis-tap survivable and is a rule about what an answer is rather than about a
drawing — so it lives in `domain/stars.ts` and not in 6.13. **Sending with everybody blank
closes the card too**, so the button says `Send no stars` rather than `Send` over an empty
body: an explicit _I am not rating anyone_ is an answer, and a player should be able to read
which one they are about to give. The write is neither optimistic nor `networkMode`-overriding
— the seven days run from the **game**, so a send held until the connection returns closes the
same card — and it **invalidates on settled rather than on success**, because the one refusal
that matters says the card was _already_ closed, which is a list this client is holding a stale
copy of.

**Ignoring a card costs nothing, and the feature is built so that nothing says otherwise.**
There is no strand for rating, no penalty and nothing recorded about a card that expired — so
there is no count of what is outstanding, no badge, no thanks and no second asking. It is also
why the card is the one read in the app that draws **nothing at all on a failed one**: the
result screen around it draws a note, because a game a player pushed into vanishing is
indistinguishable from a link gone stale and must not be, and a coral note over an unasked-for
favour is the app apologising for a chore it invented.
