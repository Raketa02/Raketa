import {
  FRIENDS_COPY,
  askForALevelLabel,
  askedForALevelLabel,
  askedYouTab,
  friendsRowLine,
  groupCountsLine,
  levelAskLine,
  levelAsksHeading,
  notNowLevelAskLabel,
  getYourLevelLabel,
  setAsideToast,
  wantToPlay,
  youReOnQuestion,
  requestsHeading,
  sportsLine,
  wantsToBeYourFriend,
  whereLine,
} from './friendsCopy';

describe('the request card’s words (§29.2)', () => {
  it('names who asks, whole', () => {
    expect(wantsToBeYourFriend('ines.d')).toBe('ines.d wants to be your friend');
  });

  it('says where, the sport and the Level, before the chip', () => {
    expect(
      whereLine({
        byLink: false,
        group: { name: 'Kazimierz crew' },
        sportName: 'Padel',
        level: 3.4,
      }),
    ).toBe('With you in Kazimierz crew · Padel 3,40 ·');
  });

  it('reads Invited you to Raketa for a link’s request', () => {
    expect(whereLine({ byLink: true })).toBe('Invited you to Raketa');
  });

  it('reads Found you in the padel ranking for a request from the ranking, in the group line’s place', () => {
    expect(whereLine({ byLink: false, ranking: 'padel', sportName: 'Padel', level: 3.4 })).toBe(
      'Found you in the padel ranking',
    );
  });

  it('reads Found you among new players for a request from New in Raketa, in the group line’s place (#801)', () => {
    expect(whereLine({ byLink: false, newPlayers: true, group: { name: 'Kazimierz crew' } })).toBe(
      'Found you among new players',
    );
  });

  it('says only what the wire named — a group they left, a sport they hold no Level in', () => {
    expect(whereLine({ byLink: false, sportName: 'Padel' })).toBe('Padel ·');
    expect(whereLine({ byLink: false, group: { name: 'Kazimierz crew' } })).toBe(
      'With you in Kazimierz crew ·',
    );
    expect(whereLine({ byLink: false })).toBe('');
  });

  it('counts the row’s title', () => {
    expect(requestsHeading(1)).toBe('Friend requests · 1');
  });
});

describe('a request refused (§30.8, §31.13)', () => {
  it('has no sentence for a daily limit, nor for the code the new rule renamed — there is neither (#799)', () => {
    expect(FRIENDS_COPY.refused['daily_request_limit']).toBeUndefined();
    expect(FRIENDS_COPY.refused['player_not_in_your_groups']).toBeUndefined();
    // The unnamed refusal says nothing: it is the state moving, and the record read again answers.
    expect(FRIENDS_COPY.refused['player_unavailable']).toBeUndefined();
  });

  it('sends a player who blocked somebody to You › Blocked players, where Unblock is now', () => {
    expect(FRIENDS_COPY.refused['unblock_them_first']).toBe(
      'You blocked this player. Unblock them in You › Blocked players first.',
    );
  });
});

describe('the Friends page’s words (§29.3)', () => {
  it('counts Asked you while a request waits, and says the name alone at nought', () => {
    expect(askedYouTab(2)).toBe('Asked you · 2');
    expect(askedYouTab(1)).toBe('Asked you · 1');
    expect(askedYouTab(0)).toBe('Asked you');
  });

  it('names every sport a friend plays with its Level, joined by a dot', () => {
    expect(
      sportsLine([
        { name: 'Padel', level: 2.75 },
        { name: 'Tennis', level: 3.1 },
      ]),
    ).toBe('Padel 2,75 · Tennis 3,10');
    expect(sportsLine([])).toBe('');
  });

  // #758: the picker's ask, with no pronoun about another player (ADR-0096).
  it('asks a greyed row’s friend to get a Level in the sport, and says Asked once asked', () => {
    expect(askForALevelLabel('zofia.b', 'padel')).toBe('Ask zofia.b to get a padel level');
    expect(FRIENDS_COPY.picker.asked).toBe('Asked');
    expect(askedForALevelLabel('zofia.b', 'padel')).toBe('Asked zofia.b to get a padel level');
  });

  it('has a one-line empty state per tab', () => {
    expect(FRIENDS_COPY.page.empty).toEqual({
      friends: 'No friends yet. Add them from your groups, or send your link.',
      ASKED_YOU: 'Nobody has asked you yet.',
      YOU_ASKED: "You haven't asked anyone.",
    });
  });
});

describe('the Add friends sheet’s words (§29.3)', () => {
  it('counts members and who is left to add, in the singular and at nought', () => {
    expect(groupCountsLine(8, 2)).toBe('8 members · 2 to add');
    expect(groupCountsLine(8, 1)).toBe('8 members · 1 to add');
    expect(groupCountsLine(8, 0)).toBe('8 members · nobody to add');
    expect(groupCountsLine(1, 0)).toBe('1 member · nobody to add');
  });
});

describe('the You tab’s Friends row', () => {
  it('counts your friends, and who asked you while anybody waits', () => {
    expect(friendsRowLine(0, 0)).toBe('No friends yet');
    expect(friendsRowLine(1, 0)).toBe('1 friend');
    expect(friendsRowLine(3, 0)).toBe('3 friends');
    expect(friendsRowLine(3, 1)).toBe('3 friends · 1 asked you');
    expect(friendsRowLine(0, 2)).toBe('No friends yet · 2 asked you');
  });
});

describe('ASKED FOR A LEVEL’s words (§29.5)', () => {
  it('counts the row’s title by sports', () => {
    expect(levelAsksHeading(2)).toBe('Asked for a level · 2');
  });

  it('names one asker, two, and two and the rest counted — never a pronoun but they', () => {
    expect(wantToPlay(['tomek.k'], 'padel')).toBe('tomek.k wants to play padel with you');
    expect(wantToPlay(['tomek.k', 'kuba.w'], 'padel')).toBe(
      'tomek.k and kuba.w want to play padel with you',
    );
    expect(wantToPlay(['tomek.k', 'kuba.w', 'ania.m', 'ewa.s'], 'padel')).toBe(
      'tomek.k, kuba.w and 2 more want to play padel with you',
    );
    expect(levelAskLine(['tomek.k'])).toBe('A few questions, and tomek.k can add you to a game.');
    expect(levelAskLine(['tomek.k', 'kuba.w'])).toBe(
      'A few questions, and they can add you to a game.',
    );
    expect(levelAskLine(['tomek.k', 'kuba.w', 'ania.m'])).toBe(
      'A few questions, and they can add you to a game.',
    );
  });

  it('names the button by the sport, and the question a run left halfway is on', () => {
    expect(getYourLevelLabel('padel')).toBe('Get your padel level');
    expect(FRIENDS_COPY.levelAsks.carryOn).toBe('Carry on');
    expect(youReOnQuestion(5)).toBe("You're on question 5.");
    expect(notNowLevelAskLabel('padel')).toBe('Not now, your padel level');
  });

  it('says where the level can be got after Not now', () => {
    expect(setAsideToast('padel')).toBe(
      'You can get your padel level any time, from You › Skill passport.',
    );
  });
});
