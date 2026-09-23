/**
 * What the **deck card** reads off a candidate — the one join between the codes and the words
 * for the card that makes no case.
 *
 * `candidateFacts` serves the two cards that argue: it composes reason lines, filters them
 * against the rows drawn, and speaks the card in §20.3's order with the argument last. The deck
 * card draws no argument
 * ([ADR-0169](../../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §7) — the level, the mark, the name, the meta line, the Fit, the intro, the tags and three
 * tiles are the whole card — so its facts are a different set read once, and its spoken name is
 * composed from the same values that are drawn. Read twice — once for the body and once for the
 * label — the two could disagree without anything failing.
 *
 * **It holds no words and no rules.** The words are `deckCardPresentation`'s and
 * `playerCardPresentation`'s; the rules are `domain/onCourtMark`'s and `domain/socialTagOverlap`'s
 * (which applies `domain/deckTags`' order). What is here is the wiring between them.
 */

import { playerName } from '@/shared/formatting/playerName';
import { ON_COURT_CLAUSE } from '@/shared/ui';
import type { SocialTagOverlap } from '@/shared/vocabulary/socialTagOverlap';

import type { Candidate, SearchEnvelope } from '../../domain/candidate';
import { wearsOnCourtMark } from '../../domain/onCourtMark';
import { socialTagOverlap } from '../../domain/socialTagOverlap';
import { deckCardLabel } from '../accessibilityPresentation';
import {
  deckMetaLine,
  deckTileClauses,
  deckTiles,
  quotedIntro,
  type DeckTile,
} from '../deckCardPresentation';
import { socialTagClauses } from '../playerCardPresentation';

import { evidenceOf } from './candidateFacts';

/** Everything the deck card draws about its subject, resolved once, and the spoken name over it. */
export interface DeckCardFacts {
  /** §15's `playerName()` — the whole handle, and a type that will not take a shortened one. */
  readonly name: string;
  /** Whether the mark is drawn — `wearsOnCourtMark`'s one answer, drawn and spoken. */
  readonly onCourt: boolean;
  /** The meta line, or nothing where neither the distance nor the week is known. */
  readonly meta: string | undefined;
  /** The intro inside its quotation marks, or nothing where they wrote none. */
  readonly intro: string | undefined;
  /** The Social tag overlap with the shared tags first. */
  readonly tags: SocialTagOverlap;
  /** Always three. */
  readonly tiles: readonly DeckTile[];
  /** The card body's spoken name. */
  readonly label: string;
}

export function deckCardFacts(candidate: Candidate, envelope: SearchEnvelope): DeckCardFacts {
  const name = playerName({ kind: 'player', name: candidate.card.name });
  const { level, band, range } = candidate.card;
  // Read once for both registers: the mark is the one thing on this card whose absence has two
  // causes, and two reads of it are two chances to fold them differently.
  const onCourt = wearsOnCourtMark(candidate.card);
  const meta = deckMetaLine({
    ...(candidate.distanceKm === undefined ? {} : { km: candidate.distanceKm }),
    theirAreaCode: candidate.card.areaCode,
    myAreaCode: envelope.myAreaCode,
    // The code's own words, drawn only on the code — ADR-0107 §3 intact.
    aroundThisWeek: candidate.livenessReasons.includes('RECENT_ACTIVITY'),
  });
  const intro = candidate.card.intro === undefined ? undefined : quotedIntro(candidate.card.intro);
  const tags = socialTagOverlap(candidate, 'shared-first');
  const tiles = deckTiles({
    balancePct: evidenceOf(candidate, 'predicted_balance')?.pct,
    playerScore: candidate.card.playerScore,
    sharedSlots: evidenceOf(candidate, 'availability_overlap')?.sharedCount,
  });

  return {
    name,
    onCourt,
    meta,
    intro,
    tags,
    tiles,
    label: deckCardLabel({
      name,
      fit: candidate.fit,
      level: { level, band, range },
      ...(onCourt ? { onCourt: ON_COURT_CLAUSE } : {}),
      ...(meta === undefined ? {} : { meta }),
      ...(intro === undefined ? {} : { intro }),
      socialTags: socialTagClauses(tags),
      tiles: deckTileClauses(tiles),
    }),
  };
}
