from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock
from app.modules.groups.application.commands import EditGroupCommand
from app.modules.groups.application.membership import group_of_a_member
from app.modules.groups.application.read_group import GroupPages
from app.modules.groups.application.views import EditedGroup, face_of
from app.modules.groups.domain.errors import NotTheGroupOwner
from app.modules.groups.domain.ports import GroupDirectory, GroupFaces, GroupRepository
from app.modules.groups.domain.value_objects import GroupName


class EditGroup:
    """The Owner saves *Edit group*: a new name, who can join, or both
    (``docs/adr/0183`` §2, §7).

    **One Save, one answer**: both are recorded or neither is, so a name
    refused under its field leaves the policy where it was too. Refused in the
    order a person could meet them — a stranger ``group_not_found``, a member
    who is not the Owner ``not_the_group_owner``, and only then the name,
    ``group_name_invalid`` under ``name`` — so a member is never told what is
    wrong with a name they may not give. Saving what the group already says
    records nothing.

    **Switching to *Anyone* admits everybody waiting at once**, and the answer
    names who it let in, in the order they asked — the Edit screen shows them.

    **The answer is drawn before the commit.** The page reads the block state,
    which fails closed; read after the commit, a failure there would answer a
    ``503`` for an edit that had happened, and the retry it invites would save
    nothing and name nobody admitted. Drawn inside the transaction, it rolls the
    edit back instead, and the retry is the whole edit again. ``save`` has
    flushed everything it wrote, so the directory already reads it.
    """

    def __init__(
        self,
        *,
        groups: GroupRepository,
        directory: GroupDirectory,
        pages: GroupPages,
        faces: GroupFaces,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._groups = groups
        self._directory = directory
        self._pages = pages
        self._faces = faces
        self._uow = uow
        self._clock = clock

    async def execute(self, command: EditGroupCommand) -> EditedGroup:
        group = await group_of_a_member(
            self._groups, command.group_id, command.editor_id
        )
        if group.owner_id != command.editor_id:
            raise NotTheGroupOwner()
        name = GroupName(command.name)

        now = self._clock.now()
        group.rename(name, by=command.editor_id, occurred_at=now)
        admitted = group.change_join_policy(
            command.join_policy, by=command.editor_id, occurred_at=now
        )
        await self._groups.save(group)

        listing = (await self._directory.listings([group.id]))[group.id]
        page = await self._pages.page(listing, reader_id=command.editor_id)
        faces = await self._faces.faces_of(admitted)
        await self._uow.commit()
        return EditedGroup(
            page=page,
            admitted=tuple(face_of(faces, player_id) for player_id in admitted),
        )
