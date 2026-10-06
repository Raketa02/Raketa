/**
 * §23's sentences, and the two the values decide.
 *
 * It asserts the **sentences** because they are the copy deck — a code with no words does not
 * compile, but a code with the *wrong* words compiles perfectly — and it asserts the two places
 * where a value this build cannot read has to leave a named gap rather than a guess.
 */

import { OUT_OF_DATE_GAP } from '@/shared/vocabulary/outOfDate';

import type { SystemLine } from '../domain/entry';
import type { ConversationMember, ConversationPerson } from '../domain/membership';

import {
  OPEN_THE_CHAT,
  WAITING_FOR_OTHERS,
  headerSubline,
  headerTitle,
  ROOM_OVER_LINE,
  systemLineSentence,
  typingLine,
} from './conversationPresentation';
import { conversationHeaderLabel } from './conversationAccessibility';

const TOMEK: ConversationMember = { playerId: 'tomek', name: 'tomek.p' };
const OLA: ConversationMember = { playerId: 'ola', name: 'ola.k' };
const MEMBERS = [TOMEK, OLA];
/** Somebody who said no to this court: named by the response, and never a member. */
const BO: ConversationPerson = { playerId: 'bo', name: 'bo' };

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

/** The stream's reading of one line. */
function said(over: Partial<SystemLine> = {}): string {
  return systemLineSentence(line(over), MEMBERS);
}

describe('the nine sentences', () => {
  it('names an acceptance, an invitation and a game that was played', () => {
    expect(said({ code: 'SEAT_ACCEPTED' })).toBe('tomek.p is in');
    expect(said({ code: 'SEATS_INVITED', values: { count: '2' } })).toBe('tomek.p asked 2 more');
    expect(said({ code: 'GAME_PLAYED' })).toBe('tomek.p said you played');
  });

  /**
   * One code, three facts. A lapse is not a decline, and since ADR-0162 leaving a game you had
   * agreed to is neither — the second clause is the same news each way.
   */
  it('keeps a decline, a lapse and a departure apart, and says the same thing about the seat', () => {
    const declined = said({ code: 'SEAT_LEFT', values: { departure: 'DECLINED' } });
    const lapsed = said({ code: 'SEAT_LEFT', values: { departure: 'LAPSED' } });
    const left = said({ code: 'SEAT_LEFT', values: { departure: 'LEFT' } });

    expect(declined).toBe('tomek.p said no — that seat is open again');
    expect(lapsed).toBe("tomek.p's day ran out — that seat is open again");
    expect(left).toBe('tomek.p left — that seat is open again');
    expect(new Set([declined, lapsed, left]).size).toBe(3);
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

  /**
   * The one plan line with no value: the three slots are the value and the room already holds a
   * line for each, so `{name} locked the plan` is the whole sentence (§23, ADR-0155).
   */
  it('names who locked the plan, and quotes no value', () => {
    expect(said({ code: 'PLAN_LOCKED' })).toBe('tomek.p locked the plan');
    expect(said({ code: 'PLAN_LOCKED', values: { value: '18:00' } })).toBe(
      'tomek.p locked the plan',
    );
  });

  /**
   * The one line a room is *born* with, and only a doubles room: two yeses that met in a doubles
   * sport seat both people on one side with a whole side still to fill
   * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
   * §8). It names nobody — it is about both people on the side — so the sentence is whole with
   * no actor and no value, and an actor the wire happens to send is not read.
   */
  it('says the two are a side, naming nobody and quoting nothing', () => {
    const side = 'You two are a side. Fill the seats to find your opponents.';

    expect(said({ code: 'SIDE_FORMED', actorId: undefined })).toBe(side);
    expect(said({ code: 'SIDE_FORMED', values: { value: 'x' } })).toBe(side);
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
      'PLAN_LOCKED',
      'SIDE_FORMED',
    ] as const;

    for (const code of everything) {
      expect(
        said({ code, values: { count: '2', departure: 'DECLINED', value: '2026-09-12' } }),
      ).not.toMatch(/game on/i);
    }
  });
});

describe('who a line names', () => {
  it('fills the slot from the people the row holds, and never from the values', () => {
    expect(said({ actorId: 'ola', values: { name: 'somebody.else' } })).toBe('ola.k is in');
  });

  /**
   * **The line a roster lookup could never name** ([#409](https://github.com/Raketa02/Raketa/issues/409)).
   * A *no* is not an accepted seat, so the actor of a `SEAT_LEFT` line was never a member — and a
   * roster lookup drew `? said no`. The line reads `people`, which names them.
   */
  it('names a departed player off the people, though they are not a member', () => {
    const declined = line({ code: 'SEAT_LEFT', actorId: 'bo', values: { departure: 'DECLINED' } });

    expect(systemLineSentence(declined, [...MEMBERS, BO])).toBe(
      'bo said no — that seat is open again',
    );
  });

  /**
   * Two states, one `?`: a line with no actor, and an actor `users` can no longer name. Neither
   * has a word to draw, and the sentence names nobody rather than inventing one.
   */
  it('names nobody for an actor the room cannot answer for', () => {
    expect(said({ actorId: undefined })).toBe('? is in');
    expect(systemLineSentence(line({ actorId: 'gone' }), [{ playerId: 'gone' }])).toBe('? is in');
  });

  /** A third-person record read identically by everybody in the room. */
  it('names the reader by their own handle rather than as *You*', () => {
    const me: ConversationMember = { playerId: 'me', name: 'me_' };

    expect(systemLineSentence(line({ actorId: 'me' }), [me, TOMEK])).toBe('me_ is in');
  });
});

describe('a plan line a room still holds', () => {
  /**
   * The old loop's plan lines are written by nothing now (#576), and a room that holds one still
   * draws it: the place as it was typed, court and all.
   */
  it('prints the place whole', () => {
    const place = line({ code: 'PLACE_RECORDED', values: { value: 'Zabłocie Sport, court 3' } });

    expect(systemLineSentence(place, MEMBERS)).toBe(
      'tomek.p set the place · Zabłocie Sport, court 3',
    );
  });
});

describe('what this build cannot read', () => {
  it('draws the named gap for a code it has no words for', () => {
    expect(systemLineSentence(line({ code: undefined }), MEMBERS)).toBe(OUT_OF_DATE_GAP);
  });

  /**
   * One rule, not two: a system line **is** the whole of its slot, so a value it cannot read
   * leaves exactly the nothing a code it cannot read does.
   */
  it('draws the same gap for a value it cannot read, rather than guessing at the sentence', () => {
    expect(said({ code: 'SEAT_LEFT', values: { departure: 'WITHDRAWN' } })).toBe(OUT_OF_DATE_GAP);
    expect(said({ code: 'SEATS_INVITED', values: {} })).toBe(OUT_OF_DATE_GAP);
    expect(said({ code: 'DAY_RECORDED', values: { value: 'Saturday' } })).toBe(OUT_OF_DATE_GAP);
    expect(said({ code: 'HOUR_RECORDED', values: {} })).toBe(OUT_OF_DATE_GAP);
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

  /**
   * **The organiser alone again** — somebody joined and left while the rest were still deciding
   * ([#429](https://github.com/Raketa02/Raketa/issues/429) E4). There is nobody to name, and a
   * blank at `h1` over *Padel* is a gap rather than a title; the line says what the room is
   * doing instead.
   */
  it('says the room is waiting where there is nobody else to name', () => {
    expect(headerTitle([], ROOM_ENOUGH)).toBe(WAITING_FOR_OTHERS);
    expect(WAITING_FOR_OTHERS).toBe('Waiting for others to join');
  });
});

describe('the header’s second line', () => {
  it('is the sport and the booking’s word, lower case', () => {
    expect(headerSubline('Padel', 'booked')).toBe('Padel · booked');
  });

  /** With no word, no state is invented. */
  it('is the sport alone where there is no word', () => {
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

  /** The drawn line's sentence is the spoken one too: there is no handle to keep whole. */
  it('speaks the waiting line where there is nobody else to name', () => {
    expect(conversationHeaderLabel([], 'Padel', undefined)).toBe(
      'Waiting for others to join, Padel',
    );
  });
});

describe('somebody is typing', () => {
  const ZOFIA: ConversationMember = { playerId: 'zofia', name: 'zofia.b' };
  const FOUR = [TOMEK, OLA, ZOFIA, { playerId: 'me', name: 'me_' }];

  /**
   * §22.5's three shapes: a name, two names, and a count from three. **Named, and named in a pair
   * too** — a pair has one possible typist and the name adds nothing a listener does not know,
   * but *somebody is typing* would be a second sentence kept only to withhold it, and the drawn
   * bubble carries no name at all, so the spoken one is where the name goes (§20.4).
   */
  it('names one person, names two, and counts from three', () => {
    expect(typingLine(['tomek'], FOUR)).toBe('tomek.p is typing…');
    expect(typingLine(['tomek', 'ola'], FOUR)).toBe('tomek.p and ola.k are typing…');
    expect(typingLine(['tomek', 'ola', 'zofia'], FOUR)).toBe('3 people are typing…');
  });

  /**
   * The whole handle, never a first name (ADR-0107), filled from **membership** and never the
   * frame — the roster and not `people`, because a typist is gated on membership and is one
   * (ADR-0156). Somebody who left the court cannot be typing in it.
   */
  it('fills names from the members the room holds, and draws ? for one it cannot', () => {
    expect(typingLine(['nobody-here'], MEMBERS)).toBe('? is typing…');
  });

  /** The ellipsis is one character, so a screen reader does not read *dot dot dot*. */
  it('ends in one character rather than three', () => {
    expect(typingLine(['tomek'], MEMBERS)).toMatch(/…$/);
    expect(typingLine(['tomek'], MEMBERS)).not.toMatch(/\.\.\./);
  });

  it('says nothing about nobody', () => {
    expect(typingLine([], MEMBERS)).toBeUndefined();
  });
});

/**
 * **The chat has ended, and the room is still on screen** — §22.5's fourth state. A booked room
 * ends with its game, and why is the game card's to say: the sentence says only that it ended,
 * and never that a seat is open again.
 */
describe('the chat has ended', () => {
  it('says only that the chat has ended', () => {
    expect(ROOM_OVER_LINE).toBe('This chat has ended.');
    expect(ROOM_OVER_LINE).not.toMatch(/open again/);
  });
});
