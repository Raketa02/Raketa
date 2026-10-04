"""The Groups context: the crowd that already plays together, at a home club.

Settled by ``docs/adr/0183``. A **Group** is one event-sourced aggregate of two
kinds — a **Player group**, which a player creates and runs as its Owner, and an
**Official group**, which an Administrator runs for their club (#509) — with
synchronous projections for groups and group members written in the act's own
transaction, the way ``users`` and ``clubs`` are.

It reads four other contexts and writes none of them, each through a port it
declares in its own words (``domain/ports.py``): **clubs** for the home club and
home-club search, **rating** for the sport dots, **users** and the Player profile
for a member's face, and the Player profile for the reader's Location area.
Besides those, its domain borrows two pure functions and nothing else — clubs'
``fold`` and the matcher's distance print — and says why where it does
(``domain/home_club_search.py``).
"""
