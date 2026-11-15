"""Discovery spells the reader's relation in its own words and puts it on the
wire as Friends' ``FriendRelation`` (#793): the two must stay one vocabulary,
value for value, or a tile's button would read a state Friends never sent."""

from app.modules.discovery.domain.relation import Relation
from app.modules.friends.domain.relation import FriendRelation


def test_discovery_spells_every_relation_friends_does():
    assert {one.value for one in Relation} == {one.value for one in FriendRelation}
