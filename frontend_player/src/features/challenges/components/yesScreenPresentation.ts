/**
 * What the yes screen says — **two words, a small `vs`, two spoken sentences, and a door**
 * ([ADR-0167](../../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
 * §1, §4; [#433](https://github.com/Raketa02/Raketa/issues/433),
 * [#434](https://github.com/Raketa02/Raketa/issues/434)).
 *
 * Copy is code, and this deck is deliberately short: the screen draws no names, no sport, no
 * day and no place, because *after accepting, a player already knows who they will play with*.
 * What is here is the word for each face, the join between the two sides, the sentence a
 * listener gets in place of the picture on each face, and the second door. The first door's
 * words are the conversation feature's `OPEN_THE_CHAT`, exactly as every other chat door's are.
 *
 * ## The sentence is built from whole handles, and never from the initials
 *
 * The tile draws two initials over a poster, and that drawing is ADR-0167 §3's one exception
 * to ADR-0107 §4 — argued on the line that a drawing invents no sentence. **This file is where
 * that line is held**: the announcement names everybody by the handle they typed, says *an
 * empty seat* where one is, and says `?` for a seat the record cannot name, which is
 * `playerName`'s own answer. The day the initials appear in a sentence, §3's fence has fallen.
 *
 * ## Two faces, keyed by which yes it is
 *
 * *Challenge!* is the word after *I'm in* whatever standing the reply came back with — singles
 * or doubles, even when this yes completed the court. *Game on!* for the completing yes was
 * refused: one word for one act (§4). ***Matched!*** is the word after a mutual, and **the one
 * place the word appears** — the past tense of *Match me*, said once, on this screen, in every
 * sport (§4); its sentence says only *you and them*, never *against* and never an empty seat,
 * because in tennis the two are opponents and in padel partners with a side to fill, and both
 * are true of the two people. The noun stays out: nothing here calls a game a match.
 */

import { playerName } from '@/shared/formatting/playerName';

import type { YesSeat, YesSides } from '../domain/yesScreen';
import type { WhichYes } from '../schemas/routeParams';

/** The one lime word after *I'm in*. */
export const CHALLENGE_WORD = 'Challenge!';

/** The one lime word after a mutual — and the one place the app says it (ADR-0167 §4). */
export const MATCHED_WORD = 'Matched!';

/**
 * The word, keyed by which yes this is — a `Record` over the union, so a third face fails to
 * compile until it has its word, rather than drawing the wrong one.
 */
export const YES_WORD: Readonly<Record<WhichYes, string>> = {
  challenge: CHALLENGE_WORD,
  mutual: MATCHED_WORD,
};

/** Between the two sides. Drawn small and grey, and never spoken: the sentence says *against*. */
export const VS = 'vs';

/** The second door — back to the Chats list. Android back is this. */
export const LATER = 'Later';

/** What an empty seat is called in the sentence, once per seat. */
const AN_EMPTY_SEAT = 'an empty seat';

/**
 * The screen's accessibility announcement and its header's label, built from whole handles.
 *
 * *Challenge! You and Ola.N against Kuba.W and Zofia.B* — the reader is *You*, a partner or an
 * empty seat follows with *and*, and the other side is joined the same way after *against*.
 * The reader is always first in `yours`, so the sentence never has to look for them.
 */
export function yesAnnouncement(sides: YesSides): string {
  const [, ...partners] = sides.yours;
  const yours = [playerName({ kind: 'you' }), ...partners.map(spoken)].join(AND);
  const theirs = sides.theirs.map(spoken).join(AND);
  return `${CHALLENGE_WORD} ${yours} ${AGAINST} ${theirs}`;
}

/**
 * The mutual's announcement and header label — *Matched! You and Marek.P* — you, then everybody
 * else who has said yes, joined with *and* and nothing else. There is no *against* because the
 * picture takes no side, and no empty seat because the picture draws none (ADR-0167 §4).
 */
export function matchedAnnouncement(sides: YesSides): string {
  const you = playerName({ kind: 'you' });
  return `${MATCHED_WORD} ${[you, ...sides.theirs.map(spoken)].join(AND)}`;
}

/**
 * The sentence, keyed by which yes this is — a `Record` over the same union as the word, for
 * the same reason: one face, one word, one sentence, and a third fails to compile without all
 * three.
 */
export const YES_SENTENCE: Readonly<Record<WhichYes, (sides: YesSides) => string>> = {
  challenge: yesAnnouncement,
  mutual: matchedAnnouncement,
};

/** The two joins the sentence is built with. */
const AND = ' and ';
const AGAINST = 'against';

function spoken(seat: YesSeat): string {
  if (seat.kind === 'empty') return AN_EMPTY_SEAT;
  return playerName(
    seat.nickname === undefined ? { kind: 'unknown' } : { kind: 'player', nickname: seat.nickname },
  );
}
