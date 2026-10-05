"""The Bookings context: a game that filled, on a court at a club (#541).

Settled by ``docs/adr/0189`` §2, §4–§5 and specified in the mechanics §11–§12.
**The last yes books the game**: every seat is charged together on the club's
account, or nobody is, and a **Booking** opens — the club, the court and its
number, the seats and their sides, the cut-off — which opens today's ordinary
**Game**, whose result, stars and record are unchanged, and whose chat opens
with the players as members.

**Event-sourced, one stream per filled proposal, filed under the proposal's own
id**, so a game keeps one id from the first card to the court. The court hours
a booking holds are what a club can no longer sell (``clubs``' ``CourtBookings``,
answered here), and a player's booked games are what *games per week* and *one
game per hour* count (``proposals``' ``BookedGames``).

Only Raketa and Instant clubs here; On request (*waiting for the club*) is #543,
and leaving, the cut-off, rescues and the club's bookings follow it.
"""
