import type { Handover } from '@/features/auth/types';

import { nextHandoverNotice } from './handovers';

const OGRODY = { clubId: 'club-o', clubName: 'Ogrody 33' };
const BONARKA = { clubId: 'club-b', clubName: 'Bonarka Arena' };

function handed(club: typeof OGRODY, groupId: string, groupName: string, waiting = 0): Handover {
  return { ...club, groupId, groupName, waitingCount: waiting };
}

describe('nextHandoverNotice', () => {
  it('tells nothing when nothing was handed', () => {
    expect(nextHandoverNotice([], [])).toBeUndefined();
  });

  it('tells one group, with the queue it came with', () => {
    expect(nextHandoverNotice([handed(OGRODY, 'g1', 'Ogrody 33 Club', 2)], [])).toEqual({
      clubId: 'club-o',
      clubName: 'Ogrody 33',
      groups: [{ groupId: 'g1', groupName: 'Ogrody 33 Club', waitingCount: 2 }],
    });
  });

  it('tells every group one club handed at once, in the order the server lists them', () => {
    const notice = nextHandoverNotice(
      [handed(OGRODY, 'g1', 'QA Tennis Only'), handed(OGRODY, 'g2', 'QA Big Group')],
      [],
    );

    expect(notice?.groups.map((group) => group.groupName)).toEqual([
      'QA Tennis Only',
      'QA Big Group',
    ]);
  });

  it('tells the club of the oldest handover first, and the other club after', () => {
    const handovers = [
      handed(BONARKA, 'b1', 'Bonarka weekend'),
      handed(OGRODY, 'g1', 'Ogrody 33 Club'),
      handed(BONARKA, 'b2', 'Bonarka nights'),
    ];

    expect(nextHandoverNotice(handovers, [])?.groups.map((group) => group.groupId)).toEqual([
      'b1',
      'b2',
    ]);
    expect(nextHandoverNotice(handovers, ['b1', 'b2'])?.clubName).toBe('Ogrody 33');
  });

  it('leaves out what was closed this launch, though the server still lists it', () => {
    expect(nextHandoverNotice([handed(OGRODY, 'g1', 'Ogrody 33 Club')], ['g1'])).toBeUndefined();
  });
});
