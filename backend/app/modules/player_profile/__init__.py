"""The Player profile context — everything a matchmaker needs that a
questionnaire cannot infer (``docs/adr/0089``).

Today this module holds only the two facts the platform *serves* about profiles:
the Social tag vocabulary and the Search radius bounds. The aggregate, its events
and the commit that creates one arrive with the context's own ticket.
"""
