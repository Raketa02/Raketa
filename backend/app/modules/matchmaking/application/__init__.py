"""The Matchmaking context's application layer.

No use cases since the searches, the deck and the radar went (#579). What is
left is the orchestration the outward ports need — **performing a read under the
posture its port declared** (``outward_reads.py``) — and the three account gates
the player record asks before it shows one player to another
(``fail_closed_gates.py``).
"""
