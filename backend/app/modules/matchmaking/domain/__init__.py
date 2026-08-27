"""The matcher's own language, and the facts it demands of everybody else.

Most of a ``domain/`` package is aggregates. This one begins as **ports**,
because the matchmaking context's first obligation is outward: five contexts owe
it facts, four of them do not exist, and ``docs/adr/0098`` makes each demand an
executable contract rather than a paragraph somebody will read months late.
"""
