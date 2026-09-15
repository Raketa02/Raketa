/**
 * **What the card says, and the tables that decide it**: the tag's word, the stage's dot, the
 * accent, the wide door's verb, the sport word, the one line the card keeps, and the three slots
 * as a listener hears them.
 *
 * The ladder is `ladder.test.ts`'s and the fold is `gameCard.test.ts`'s; what is asserted here is
 * only the words and the tables, against the copy deck rather than against strings wherever a
 * sentence has a home. Every table is walked over **all nine names**, because a name with no row
 * is the drift a `Record` over the union exists to refuse
 * ([#413](https://github.com/Raketa02/Raketa/issues/413)).
 */

import { gameStandingLine, type Game } from '@/features/games/types';
import { theme } from '@/shared/ui';
import { FILL_THE_SEAT, WE_PLAYED } from '@/shared/vocabulary/theActsWords';

import { GAME_CARD_NAMES, doorOf } from '../domain/gameCard';
import type { Plan } from '../domain/slots';

import {
  ACCENT,
  CARD_TAG,
  FINISH_THE_PLAN,
  GAMES_HEADING,
  STAGE_DOT,
  cardLine,
  cardSlotSpoken,
  cardStateWord,
  doorLabel,
  gameCardLabel,
  gamesHeading,
  sportSpoken,
  sportWord,
} from './nowPresentation';
import { NOT_AGREED_YET, SLOT_EYEBROW, TODAY } from './planPresentation';

const GAME_ID = '11111111-0000-4000-8000-000000000001';
const READ_AT = '2026-09-12T09:00:00Z';

const SINGLES_SEATS: Game['seats'] = [
  { side: 'A', playerId: 'me', name: 'me_' },
  { side: 'B', playerId: 'them', name: 'tomek.p' },
];

/** A doubles court after two people left: two seats open. */
const TWO_SHORT: Game['seats'] = [
  { side: 'A', playerId: 'me', name: 'me_' },
  { side: 'A' },
  { side: 'B', playerId: 'them', name: 'tomek.p' },
  { side: 'B' },
];

function game(over: Partial<Game> = {}): Game {
  return {
    gameId: GAME_ID,
    challengeId: '22222222-0000-4000-8000-000000000002',
    sport: 'padel',
    standing: 'AWAITING_ENTRY',
    seats: SINGLES_SEATS,
    plannedAt: '2026-09-08T09:00:00Z',
    entryClosesAt: '2026-09-19T09:00:00Z',
    proposals: [],
    readAt: READ_AT,
    ...over,
  };
}

function plan(over: Partial<Plan> = {}): Plan {
  return {
    challengeId: '22222222-0000-4000-8000-000000000002',
    anchor: '2026-09-08T09:00:00Z',
    ...over,
  };
}

describe('the heading', () => {
  it('carries the count, which is the one number on this screen', () => {
    expect(gamesHeading(3)).toBe(`${GAMES_HEADING} · 3`);
  });
});

describe('the tag', () => {
  it('names every card this build can draw, and none it cannot', () => {
    const named = GAME_CARD_NAMES.filter((name) => CARD_TAG[name] !== undefined);

    expect(named).toHaveLength(GAME_CARD_NAMES.length - 1);
    expect(CARD_TAG.unreadable).toBeUndefined();
  });
});

/**
 * **The dot is the stage's** (#413) — the one surface on which a `Tag`'s dot is not a sport's,
 * and legal because the sport is the word beside it. Three colours, three meanings: the game is
 * still in the players' hands, the game is settled, the game is over quietly.
 */
describe('the stage dot', () => {
  it('is the arranging colour where the players still owe the game something', () => {
    for (const name of ['planning', 'needs-a-player', 'needs-result', 'confirm'] as const) {
      expect(STAGE_DOT[name]).toBe(theme.color.arranging);
    }
  });

  it('is mint where the game is settled', () => {
    for (const name of ['game-on', 'counted'] as const) {
      expect(STAGE_DOT[name]).toBe(theme.color.mint);
    }
  });

  it('is the quiet hairline on the three quiet endings, and nothing where there is no tag', () => {
    expect(STAGE_DOT.uncounted).toBe(theme.color.onDarkHair);
    expect(STAGE_DOT['never-played']).toBe(theme.color.onDarkHair);
    expect(STAGE_DOT['called-off']).toBe(theme.color.onDarkHair);
    expect(STAGE_DOT.unreadable).toBeUndefined();
  });

  it('has a row for every name the tag has a word for, and only those', () => {
    for (const name of GAME_CARD_NAMES) {
      expect(STAGE_DOT[name] === undefined).toBe(CARD_TAG[name] === undefined);
    }
  });
});

/**
 * **The accent is one table** — the settled bar's bright colour and the wide button's variant
 * come from the same row, so a card cannot draw a volt bar over a mint door.
 */
describe('the accent', () => {
  it('is volt on Planning — the plan is settled here — and the volt button under it', () => {
    expect(ACCENT.planning).toEqual({ bar: theme.color.volt, button: 'volt' });
  });

  it('is mint on every other card, until its own design arrives', () => {
    for (const name of GAME_CARD_NAMES) {
      if (name === 'planning') continue;
      expect(ACCENT[name]).toEqual({ bar: theme.color.mint, button: 'settled' });
    }
  });
});

/**
 * **The card's name in the middle of a line** — `Padel · planning` — for the one surface that
 * says it after something else ([#401](https://github.com/Raketa02/Raketa/issues/401)).
 *
 * It is a second table rather than `toLowerCase()` at the call site, because *Game on* → *game on*
 * is right and a name that ever holds a proper noun would not be; the test below is what keeps
 * the two tables in step **until** that day, and is what changes on it.
 */
describe('the card’s name in a line', () => {
  it.each([
    ['planning', 'planning'],
    ['game-on', 'game on'],
    ['needs-result', 'needs result'],
    ['needs-a-player', 'needs a player'],
    ['called-off', 'called off'],
  ] as const)('says %s as %s, in lower case', (name, word) => {
    expect(cardStateWord(name)).toBe(word);
  });

  it('is the tag’s own word, lowered, on every card the tag names — until a proper noun arrives', () => {
    for (const name of GAME_CARD_NAMES) {
      expect(cardStateWord(name)).toBe(CARD_TAG[name]?.toLowerCase());
    }
  });

  it('has no word for a standing this build cannot read, exactly as the tag has none', () => {
    expect(cardStateWord('unreadable')).toBeUndefined();
  });
});

/**
 * **The wide door's verb, per name** — `Finish the plan` on Planning, and the three verbs §22.7
 * fixed on the other rungs. Keyed by the card's name rather than by the door, because the door
 * *Planning* carries is `open` and the word on it is not.
 */
describe('the door’s word', () => {
  it('says Finish the plan on Planning, where the door is the same open as Game on’s', () => {
    expect(doorLabel('planning')).toBe(FINISH_THE_PLAN);
    expect(doorLabel('game-on')).toBe('Open');
    expect(doorOf('planning')).toBe(doorOf('game-on'));
  });

  it('keeps the act’s own verb on the score-led rung and on the argument', () => {
    expect(doorLabel('needs-result')).toBe(WE_PLAYED);
    expect(doorLabel('confirm')).toBe('Confirm the result');
  });

  /**
   * **No card says *Today*, and none but *Needs result* leads with *We played*** (ADR-0166): the
   * day of the game is the day row's to say, and *you played* leads only once the agreed point is
   * behind the fold. A table that grew the name back would draw a tag the ADR retired.
   */
  it('has no Today card, so the day of the game leads with the plan until the hour has passed', () => {
    expect((GAME_CARD_NAMES as readonly string[]).includes('today')).toBe(false);
    expect(Object.keys(CARD_TAG)).not.toContain('today');
    expect(GAME_CARD_NAMES.filter((name) => doorLabel(name) === WE_PLAYED)).toEqual([
      'needs-result',
    ]);
  });

  /**
   * **`Fill the seat`, singular** (#419): the card's door on a court somebody left. The challenge
   * screen keeps `⚡ Fill the seats` for the same act — that surface is about a court still being
   * built, and this one is about the one seat that opened.
   */
  it('says Fill the seat on Needs a player, where the door is the fill', () => {
    expect(CARD_TAG['needs-a-player']).toBe('Needs a player');
    expect(doorLabel('needs-a-player')).toBe(FILL_THE_SEAT);
    expect(FILL_THE_SEAT).toBe('Fill the seat');
    expect(doorOf('needs-a-player')).toBe('fill');
  });

  /** A word for a door the ladder does not carry would be a control the state cannot take. */
  it('has a word exactly where domain/ has a door, on all nine names', () => {
    for (const name of GAME_CARD_NAMES) {
      expect(doorLabel(name) === undefined).toBe(doorOf(name) === undefined);
    }
  });
});

describe('the sport word', () => {
  it('is the sport, and marks only a friendly', () => {
    expect(sportWord(game(), 'Padel')).toBe('Padel');
    expect(sportWord(game({ kind: 'FRIENDLY' }), 'Padel')).toBe('Padel · Friendly');
  });

  /** A kind this build cannot read drops its clause; every other word on the card stands. */
  it('draws a game whose kind it cannot read as a game', () => {
    const { kind: _dropped, ...unknown } = game({ kind: 'FRIENDLY' });

    expect(sportWord(unknown, 'Padel')).toBe('Padel');
  });

  it('is spoken as a clause, because a listener has no reading for a middle dot', () => {
    expect(sportSpoken(game(), 'Padel')).toBe('Padel');
    expect(sportSpoken(game({ kind: 'FRIENDLY' }), 'Padel')).toBe('Padel, friendly');
  });

  it('says nothing about singles or doubles — the court says the format', () => {
    const four: Game['seats'] = [
      ...SINGLES_SEATS,
      { side: 'A', playerId: 'a', name: 'ola_k' },
      { side: 'B', playerId: 'b', name: 'marekb' },
    ];

    expect(sportWord(game({ seats: four }), 'Padel')).toBe('Padel');
  });
});

/**
 * **The one line the card keeps under the slots** — the window on *Needs result*, and the standing
 * on everything that is not a rung. The three plan-led rungs draw none: the slots are their whole
 * account, and *Still to agree* became a dim bar.
 */
describe('the line under the slots', () => {
  const facts = (over: Partial<Game> = {}, agreed?: Plan) => ({
    game: game(over),
    plan: agreed,
    playerId: 'me',
  });

  it('is nothing on the two rungs whose account is the slots', () => {
    expect(cardLine('planning', facts())).toBeUndefined();
    expect(cardLine('planning', facts({}, plan({ day: '2026-09-12' })))).toBeUndefined();
    expect(
      cardLine('game-on', facts({}, plan({ place: 'x', day: '2026-09-19', hour: '18:00' }))),
    ).toBeUndefined();
  });

  it('is the time left when a result is owed', () => {
    expect(cardLine('needs-result', facts({ entryClosesAt: '2026-09-13T09:00:00Z' }))).toBe(
      '24 hours left',
    );
  });

  /** Undated, the window has closed on somebody's word that the game happened: no countdown. */
  it('is nothing on Needs result where the wire dated no window', () => {
    expect(cardLine('needs-result', facts({ entryClosesAt: undefined }))).toBeUndefined();
  });

  /**
   * Everything that is not a rung already has a sentence, and it is `features/games`' — so the
   * assertion is the citation itself, not a copy of the words: the card says exactly what the
   * screen behind it says, whatever those words become.
   */
  it('says what an ended game is, in the sentence the screen behind it says', () => {
    for (const standing of ['CONFIRMED', 'UNSCORED'] as const) {
      const ended = game({ standing });
      const name = standing === 'CONFIRMED' ? 'counted' : 'uncounted';

      expect(cardLine(name, facts({ standing }))).toBe(gameStandingLine(ended, 'me'));
    }
  });
});

/**
 * **The three slots, spoken** — each named and then what it holds, in `planTagsName`'s own
 * register: the place whole, the day with its date and as *Today* on the day, the hour as drawn,
 * and *Not agreed yet* where nothing is.
 */
describe('a slot, spoken', () => {
  it('names the slot and speaks the place whole, comma and court and all', () => {
    expect(cardSlotSpoken(plan({ place: 'Zabłocie Sport, court 3' }), 'where', READ_AT)).toBe(
      `${SLOT_EYEBROW.where}, Zabłocie Sport, court 3`,
    );
  });

  it('speaks the day as the weekday and its date', () => {
    expect(cardSlotSpoken(plan({ day: '2026-08-09' }), 'day', READ_AT)).toBe(
      `${SLOT_EYEBROW.day}, Sunday 9 Aug`,
    );
  });

  /** As the row draws it (ADR-0166): the word replaces the weekday and the date stays. */
  it('speaks the day as Today and its date, on the day the list was read', () => {
    expect(cardSlotSpoken(plan({ day: '2026-09-12' }), 'day', READ_AT)).toBe(
      `${SLOT_EYEBROW.day}, ${TODAY} 12 Sep`,
    );
    expect(cardSlotSpoken(plan({ day: '2026-09-13' }), 'day', READ_AT)).toBe(
      `${SLOT_EYEBROW.day}, Sunday 13 Sep`,
    );
  });

  it('speaks the hour as it is drawn, under the card’s word for it', () => {
    expect(cardSlotSpoken(plan({ hour: '19:00' }), 'hour', READ_AT)).toBe(
      `${SLOT_EYEBROW.hour}, 19:00`,
    );
  });

  it('says a slot nobody has filled is not agreed yet, in the drawn words', () => {
    expect(cardSlotSpoken(undefined, 'where', READ_AT)).toBe(
      `${SLOT_EYEBROW.where}, ${NOT_AGREED_YET}`,
    );
    expect(cardSlotSpoken(plan(), 'hour', READ_AT)).toBe(`${SLOT_EYEBROW.hour}, ${NOT_AGREED_YET}`);
  });
});

describe('what the card announces', () => {
  /**
   * §24.5 as amended by #413: the tag, the sport, the three slots as sentences, then the line —
   * and **no verb**, because the two doors are elements of their own now and a name ending in
   * `Open` beside a button announcing `Open` is the double announcement 6.8 refuses.
   */
  it('says the card’s name, the sport, the three slots and nothing about the door', () => {
    const said = gameCardLabel({
      name: 'planning',
      sportName: 'Padel',
      game: game(),
      plan: plan({ place: 'Zabłocie Sport, court 3' }),
      playerId: 'me',
    });

    expect(said).toBe(
      'Planning. Padel. Where, Zabłocie Sport, court 3. Day, Not agreed yet. Time, Not agreed yet.',
    );
    expect(said).not.toContain(FINISH_THE_PLAN);
  });

  it('adds the line where the card keeps one', () => {
    const said = gameCardLabel({
      name: 'counted',
      sportName: 'Padel',
      game: game({ standing: 'CONFIRMED' }),
      plan: plan({ place: 'Zabłocie Sport', day: '2026-09-11', hour: '18:00' }),
      playerId: 'me',
    });

    expect(said).toBe(
      `Counted. Padel. Where, Zabłocie Sport. Day, Friday 11 Sep. Time, 18:00. ${gameStandingLine(game({ standing: 'CONFIRMED' }), 'me')}`,
    );
  });

  /**
   * **The court is hidden from a listener, so the gap in it is said** — one clause after the
   * sport, counted, because *Needs a player* names the errand and not the shape of the court.
   */
  it('says the open seat on Needs a player, and how many when there are more', () => {
    const one = gameCardLabel({
      name: 'needs-a-player',
      sportName: 'Padel',
      game: game({ seats: [SINGLES_SEATS[0]!, { side: 'B' }] }),
      plan: undefined,
      playerId: 'me',
    });
    const two = gameCardLabel({
      name: 'needs-a-player',
      sportName: 'Padel',
      game: game({ seats: TWO_SHORT }),
      plan: undefined,
      playerId: 'me',
    });

    expect(one).toBe(
      'Needs a player. Padel. An open seat. Where, Not agreed yet. Day, Not agreed yet. Time, Not agreed yet.',
    );
    expect(two).toContain('Padel. 2 open seats. Where,');
  });

  it('says nothing about seats on a full court', () => {
    const said = gameCardLabel({
      name: 'planning',
      sportName: 'Padel',
      game: game(),
      plan: undefined,
      playerId: 'me',
    });

    expect(said).not.toMatch(/open seat/);
  });

  it('marks a friendly in the sport clause', () => {
    const said = gameCardLabel({
      name: 'game-on',
      sportName: 'Padel',
      game: game({ kind: 'FRIENDLY' }),
      plan: plan({ place: 'Zabłocie Sport', day: '2026-09-19', hour: '18:00' }),
      playerId: 'me',
    });

    expect(said).toContain('Padel, friendly.');
  });
});
