/**
 * §23's seven sentences, the two the values decide, and the one thing the row does differently.
 *
 * It asserts the **sentences** because they are the copy deck — a code with no words does not
 * compile, but a code with the *wrong* words compiles perfectly — and it asserts the two places
 * where a value this build cannot read has to leave a named gap rather than a guess.
 */

import { OUT_OF_DATE_GAP } from '@/shared/vocabulary/outOfDate';

import type { SystemLine } from '../domain/entry';
import type { ConversationMember } from '../domain/membership';

import {
  OPEN_THE_CHAT,
  conversationRowLine,
  entryLine,
  headerSubline,
  headerTitle,
  systemLineSentence,
} from './conversationPresentation';
import { conversationHeaderLabel } from './conversationAccessibility';

const TOMEK: ConversationMember = { playerId: 'tomek', nickname: 'tomek.p' };
const OLA: ConversationMember = { playerId: 'ola', nickname: 'ola.k' };
const MEMBERS = [TOMEK, OLA];

function line(over: Partial<SystemLine> = {}): SystemLine {
  return {
    kind: 'system-line',
    seq: 4,
    code: 'SEAT_ACCEPTED',
    occurredAt: '2026-09-08T12:00:00Z',
    actorId: 'tomek',
    values: {},
    ...over,
  };
}

/** The row's reading, which is the one both surfaces share except for the place. */
function said(over: Partial<SystemLine> = {}): string {
  return systemLineSentence(line(over), MEMBERS, 'one-line');
}

describe('the seven sentences', () => {
  it('names an acceptance, an invitation and a game that was played', () => {
    expect(said({ code: 'SEAT_ACCEPTED' })).toBe('tomek.p is in');
    expect(said({ code: 'SEATS_INVITED', values: { count: '2' } })).toBe('tomek.p asked 2 more');
    expect(said({ code: 'GAME_PLAYED' })).toBe('tomek.p said you played');
  });

  /** One code, two facts. A lapse is not a decline, and the second clause is the same news. */
  it('keeps a decline and a lapse apart, and says the same thing about the seat', () => {
    const declined = said({ code: 'SEAT_LEFT', values: { departure: 'DECLINED' } });
    const lapsed = said({ code: 'SEAT_LEFT', values: { departure: 'LAPSED' } });

    expect(declined).toBe('tomek.p said no — that seat is open again');
    expect(lapsed).toBe("tomek.p's day ran out — that seat is open again");
    expect(declined).not.toBe(lapsed);
  });

  it('names the three plan slots by what they are, and the day as a weekday', () => {
    expect(said({ code: 'PLACE_RECORDED', values: { value: 'Zabłocie Sport' } })).toBe(
      'tomek.p set the place · Zabłocie Sport',
    );
    expect(said({ code: 'DAY_RECORDED', values: { value: '2026-09-12' } })).toBe(
      'tomek.p set the day · Saturday',
    );
    expect(said({ code: 'HOUR_RECORDED', values: { value: '18:00' } })).toBe(
      'tomek.p set the time · 18:00',
    );
  });

  /** There is no *Game on* line: a derived standing is never announced. */
  it('says nothing anywhere about the line-up being complete', () => {
    const everything = [
      'SEAT_ACCEPTED',
      'SEATS_INVITED',
      'SEAT_LEFT',
      'GAME_PLAYED',
      'PLACE_RECORDED',
      'DAY_RECORDED',
      'HOUR_RECORDED',
    ] as const;

    for (const code of everything) {
      expect(
        said({ code, values: { count: '2', departure: 'DECLINED', value: '2026-09-12' } }),
      ).not.toMatch(/game on/i);
    }
  });
});

describe('who a line names', () => {
  it('fills the slot from the members the row holds, and never from the values', () => {
    expect(said({ actorId: 'ola', values: { name: 'somebody.else' } })).toBe('ola.k is in');
  });

  /**
   * Two states, one `?`: a line with no actor, and an actor `users` can no longer name. Neither
   * has a word to draw, and the sentence names nobody rather than inventing one.
   */
  it('names nobody for an actor the room cannot answer for', () => {
    expect(said({ actorId: undefined })).toBe('? is in');
    expect(systemLineSentence(line({ actorId: 'gone' }), [{ playerId: 'gone' }], 'one-line')).toBe(
      '? is in',
    );
  });

  /** A third-person record read identically by everybody in the room. */
  it('names the reader by their own handle rather than as *You*', () => {
    const me: ConversationMember = { playerId: 'me', nickname: 'me_' };

    expect(systemLineSentence(line({ actorId: 'me' }), [me, TOMEK], 'one-line')).toBe('me_ is in');
  });
});

describe('what the row does differently, which is a prop and not a fork', () => {
  const place = line({ code: 'PLACE_RECORDED', values: { value: 'Zabłocie Sport, court 3' } });

  it('drops the court where there is one line, and prints it where there is room', () => {
    expect(systemLineSentence(place, MEMBERS, 'one-line')).toBe(
      'tomek.p set the place · Zabłocie Sport',
    );
    expect(systemLineSentence(place, MEMBERS, 'full')).toBe(
      'tomek.p set the place · Zabłocie Sport, court 3',
    );
  });

  it('leaves a place with nothing to drop whole', () => {
    const plain = line({ code: 'PLACE_RECORDED', values: { value: 'Zabłocie Sport' } });

    expect(systemLineSentence(plain, MEMBERS, 'one-line')).toBe(
      systemLineSentence(plain, MEMBERS, 'full'),
    );
  });
});

describe('what this build cannot read', () => {
  it('draws the named gap for a code it has no words for', () => {
    expect(systemLineSentence(line({ code: undefined }), MEMBERS, 'one-line')).toBe(
      OUT_OF_DATE_GAP,
    );
  });

  /**
   * One rule, not two: a system line **is** the whole of the slot a row draws it in, so a value
   * it cannot read leaves exactly the nothing a code it cannot read does.
   */
  it('draws the same gap for a value it cannot read, rather than guessing at the sentence', () => {
    expect(said({ code: 'SEAT_LEFT', values: { departure: 'WITHDRAWN' } })).toBe(OUT_OF_DATE_GAP);
    expect(said({ code: 'SEATS_INVITED', values: {} })).toBe(OUT_OF_DATE_GAP);
    expect(said({ code: 'DAY_RECORDED', values: { value: 'Saturday' } })).toBe(OUT_OF_DATE_GAP);
    expect(said({ code: 'HOUR_RECORDED', values: {} })).toBe(OUT_OF_DATE_GAP);
  });
});

describe('a message', () => {
  it('is its own text, with nobody named in front of it', () => {
    const text = entryLine(
      {
        kind: 'message',
        seq: 9,
        authorId: 'tomek',
        sentAt: '2026-09-08T12:00:00Z',
        text: 'on my way',
        clientMessageId: 'client-1',
      },
      MEMBERS,
      'one-line',
    );

    expect(text).toBe('on my way');
  });
});

describe('a room where nothing has happened yet', () => {
  /** The opening writes no line, so there is genuinely nothing there — and no sentence for it. */
  it('has no line at all, rather than one asserting that nothing has happened', () => {
    expect(
      conversationRowLine(
        { conversationId: 'c1', challengeId: 'ch1', sport: 'padel', members: MEMBERS },
        'one-line',
      ),
    ).toBeUndefined();
  });
});

describe('the chat door', () => {
  /** *The same words as every other chat door*, which is what one constant buys. */
  it('is one sentence, owned here because what it opens is a conversation', () => {
    expect(OPEN_THE_CHAT).toBe('Open the chat');
  });
});

/**
 * **The header's two lines, and the one name it speaks**
 * ([#401](https://github.com/Raketa02/Raketa/issues/401)). The drawn title is each handle's
 * **stem** — `handleStem`, the prefix up to the first word break, which ADR-0107 permits because
 * it invents nothing — and the spoken name is every handle **whole**, which is §20.4: *the visible
 * label truncates, the spoken one never does*.
 */
describe('the header’s title line', () => {
  /** A budget no room needs, so what is asserted is the stemming and not the dropping. */
  const ROOM_ENOUGH = 80;

  it('draws one other person by their stem', () => {
    expect(headerTitle(['tomek.p'], ROOM_ENOUGH)).toBe('tomek');
  });

  it('draws two, comma-separated', () => {
    expect(headerTitle(['tomek.p', 'ola.k'], ROOM_ENOUGH)).toBe('tomek, ola');
  });

  it('draws three — a doubles room — the same way', () => {
    expect(headerTitle(['kuba.w', 'ola.k', 'zofia.b'], ROOM_ENOUGH)).toBe('kuba, ola, zofia');
  });

  /** `handleStem`'s own rule, read through this line rather than re-implemented under it. */
  it('keeps a handle with no word break whole', () => {
    expect(headerTitle(['bea_k', 'dorota-w'], ROOM_ENOUGH)).toBe('bea_k, dorota-w');
  });

  /** §15 survives: the stems are shorter inputs to the same rule, which still drops whole names. */
  it('still gives way by dropping whole names, never by cutting one', () => {
    expect(headerTitle(['aleksandra.m', 'tomek.p', 'ola.k'], 14)).toBe('aleksandra +2');
  });
});

describe('the header’s second line', () => {
  it('is the sport and the game’s state, lower case, where there is a game', () => {
    expect(headerSubline('Padel', 'planning')).toBe('Padel · planning');
  });

  /** A `LINE_UP_INCOMPLETE` room has no game and no plan, and no state is invented for it. */
  it('is the sport alone where there is no game', () => {
    expect(headerSubline('Padel', undefined)).toBe('Padel');
  });
});

describe('what the header is called', () => {
  it('names every handle whole, then the sport and the state — the row’s own dialect', () => {
    expect(conversationHeaderLabel(['tomek.p', 'ola.k'], 'Padel', 'game on')).toBe(
      'tomek.p and ola.k, Padel, game on',
    );
  });

  it('stops at the sport where there is no game', () => {
    expect(conversationHeaderLabel(['tomek.p'], 'Padel', undefined)).toBe('tomek.p, Padel');
  });
});
