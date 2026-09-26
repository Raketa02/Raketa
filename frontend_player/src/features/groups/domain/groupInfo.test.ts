import type { GroupPerson } from './group';
import {
  adminTagged,
  countMoved,
  detailsUnchanged,
  groupExit,
  membersRow,
  readerFace,
} from './groupInfo';

const face = (n: number): GroupPerson => ({ playerId: `p${n}`, name: `Member ${n}` });
const READER: GroupPerson = { playerId: 'me', name: 'Tomek Kowal' };

describe('the members row', () => {
  it('draws the faces served and counts the other members it does not draw', () => {
    const faces = [face(1), face(2), face(3), face(4), face(5)];

    expect(membersRow({ memberFaces: faces, memberCount: 8 }, READER)).toEqual({ faces, more: 2 });
  });

  it('counts nobody more when every other member is drawn', () => {
    expect(membersRow({ memberFaces: [face(1)], memberCount: 2 }, READER)).toEqual({
      faces: [face(1)],
      more: 0,
    });
  });

  // Mock 57: a reader alone draws their own face.
  it('draws the reader’s own face when they are alone', () => {
    expect(membersRow({ memberFaces: [], memberCount: 1 }, READER)).toEqual({
      faces: [READER],
      more: 0,
    });
  });

  // A block can hide everybody else: the reader stands in, and +N still counts them all.
  it('draws the reader and counts everybody else when a block hides them all', () => {
    expect(membersRow({ memberFaces: [], memberCount: 4 }, READER)).toEqual({
      faces: [READER],
      more: 3,
    });
  });

  it('draws no face at all for a reader the cache has not heard of', () => {
    expect(membersRow({ memberFaces: [], memberCount: 1 }, undefined)).toEqual({
      faces: [],
      more: 0,
    });
  });
});

describe('the reader’s own face', () => {
  const group = {
    ratedBySport: [
      { sport: 'padel' as const, ratedCount: 1, firstRated: [face(1)] },
      {
        sport: 'tennis' as const,
        ratedCount: 2,
        firstRated: [face(1), { playerId: 'me', name: 'Tomek Kowal', photoUrl: 'https://p/me' }],
      },
    ],
  };

  it('is the one a sport’s roster already holds, photograph and all', () => {
    expect(readerFace(group, 'me')).toEqual({
      playerId: 'me',
      name: 'Tomek Kowal',
      photoUrl: 'https://p/me',
    });
  });

  it('is the poster when no roster holds it', () => {
    expect(readerFace({ ratedBySport: [] }, 'me')).toEqual({ playerId: 'me', name: null });
  });

  it('is nobody for a reader the cache has not heard of', () => {
    expect(readerFace(group, undefined)).toBeUndefined();
  });
});

describe('the way out of a group', () => {
  it('is Delete for an Owner alone', () => {
    expect(groupExit({ isOwner: true, memberCount: 1 })).toBe('delete');
  });

  it('is Leave for an Owner with other members, who passes the group on', () => {
    expect(groupExit({ isOwner: true, memberCount: 2 })).toBe('leave');
  });

  it('is Leave for everybody else', () => {
    expect(groupExit({ isOwner: false, memberCount: 8 })).toBe('leave');
  });
});

describe('a refused way out', () => {
  it('means the count moved when the Owner is alone, or is not any more', () => {
    expect(countMoved('lone_owner_cannot_leave')).toBe(true);
    expect(countMoved('group_has_other_members')).toBe(true);
  });

  it('means nothing of the kind otherwise', () => {
    expect(countMoved('group_not_found')).toBe(false);
    expect(countMoved(undefined)).toBe(false);
  });
});

describe('whether Edit group has anything to save', () => {
  const group = { name: 'Kazimierz crew', joinPolicy: 'PEOPLE_I_APPROVE' as const };

  it('has nothing while the form says what the group says', () => {
    expect(
      detailsUnchanged({ name: 'Kazimierz crew', joinPolicy: 'PEOPLE_I_APPROVE' }, group),
    ).toBe(true);
  });

  it('has a new name, or a new policy', () => {
    expect(
      detailsUnchanged({ name: 'Kazimierz padel', joinPolicy: 'PEOPLE_I_APPROVE' }, group),
    ).toBe(false);
    expect(detailsUnchanged({ name: 'Kazimierz crew', joinPolicy: 'ANYONE' }, group)).toBe(false);
  });
});

describe('the admin tag on Members', () => {
  it('goes on a player group’s Owner', () => {
    expect(adminTagged({ isOwner: true, isAdministrator: false })).toBe(true);
  });

  // #519: an official group has no Owner; its Administrator who joined as a player is its admin.
  it('goes on an official group’s Administrator who joined as a player', () => {
    expect(adminTagged({ isOwner: false, isAdministrator: true })).toBe(true);
  });

  it('goes on nobody else', () => {
    expect(adminTagged({ isOwner: false, isAdministrator: false })).toBe(false);
  });
});
