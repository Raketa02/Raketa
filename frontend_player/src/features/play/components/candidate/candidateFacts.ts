/**
 * What a card reads off a candidate — the one join between the codes and the words.
 *
 * Three cards draw three shapes over one contract, and every one of them needs the same
 * answers: the person's name, the level row's facts, the meta line's, the reasons that
 * survived this surface's filter, the one concern it draws, and the spoken name composed from
 * all of them. Written per card that is the same lookup three times, and the third copy is
 * where one of them stops matching.
 *
 * **One call per render, and the spoken name is composed from the same values that are
 * drawn.** Read twice — once for the body and once for the label — the two could disagree
 * without anything failing: §20.3's whole claim is that the card is *spoken in a different
 * order than it is drawn*, which is only true if it is the same card.
 *
 * **It holds no words and no rules.** The words are `reasonPresentation`'s,
 * `livenessPresentation`'s, `concernPresentation`'s and `playerCardPresentation`'s; the rules
 * are `reasonSelection`'s. What is here is the wiring between them, including the one argument
 * `selectReasons` cannot make for itself — *can this evidence be written as a sentence at
 * all* — because that is a question about the copy and `domain/` holds none.
 */

import { playerName } from '@/shared/formatting/playerName';

import type { Candidate, SearchEnvelope } from '../../domain/candidate';
import type { Evidence } from '../../domain/evidence';
import { selectConcern, selectReasons, type ReasonSelection } from '../../domain/reasonSelection';
import type { Term } from '../../domain/vocabulary';
import { candidateCardLabel } from '../accessibilityPresentation';
import { balanceReading } from '../balancePresentation';
import { concernLine } from '../concernPresentation';
import { livenessLine } from '../livenessPresentation';
import type { LevelRowFacts, MetaLineFacts } from '../playerCardPresentation';
import { reasonLine } from '../reasonPresentation';

/**
 * Everything a card reads off one candidate, resolved once.
 *
 * The lines are already the sentences the card draws, and `label` is composed from those same
 * strings — see the module note.
 */
export interface CandidateFacts {
  /** §15's `playerName()` — the whole handle, and a type that will not take a shortened one. */
  readonly name: string;
  readonly level: LevelRowFacts;
  /** The forecast reading, on the card that **draws** it rather than saying it. */
  readonly balance: string | undefined;
  /** Omitted where the card draws no meta line, or the distance term stood down. */
  readonly meta: MetaLineFacts | undefined;
  readonly reasons: readonly string[];
  /** At most one. The rest are the why-fit sheet's. */
  readonly concerns: readonly string[];
  /** The card body's spoken name, in §20.3's order. */
  readonly label: string;
}

export function candidateFacts(
  candidate: Candidate,
  envelope: SearchEnvelope,
  drawn: readonly Term[],
): CandidateFacts {
  const name = playerName({ kind: 'player', nickname: candidate.card.nickname });
  const level = levelFactsOf(candidate);
  // A clause per row the card DRAWS — which is the drawn set read the other way round. A
  // card that says a term as a reason line must not also state it as a fact, and a card that
  // draws it as a row must state it here, because the row itself announces nothing (§20.1).
  const balance = drawn.includes('PREDICTED_BALANCE') ? balanceOf(candidate) : undefined;
  const meta = drawn.includes('DISTANCE') ? metaFactsOf(candidate, envelope) : undefined;
  const reasons = reasonLinesOf(candidate, drawn);
  const concerns = concernLinesOf(candidate);

  return {
    name,
    level,
    balance,
    meta,
    reasons,
    concerns,
    // §20.3 fixes ONE order for every card in the feature, and it is not the order they are
    // drawn in: identifying facts lead, the argument follows. A card composing its own could
    // drift from the other two, which is what §20.3 exists to stop.
    label: candidateCardLabel({
      name,
      fit: candidate.fit,
      level,
      balance,
      meta,
      reasons,
      concerns,
    }),
  };
}

/** The forecast as the card draws it, or nothing where the term stood down. */
function balanceOf(candidate: Candidate): string | undefined {
  const balance = evidenceOf(candidate, 'predicted_balance');
  return balance === undefined ? undefined : balanceReading(balance.pct);
}

/**
 * The evidence behind one of the terms a card draws **as a row**.
 *
 * Typed on the variant rather than on the term, so a card asking for the forecast gets
 * `PredictedBalanceEvidence` or nothing — never a `Evidence` it has to narrow again at the
 * call site, which is where a card would end up branching on a term after all.
 *
 * `undefined` means the term **stood down**: a degraded term is not on `terms[]` at all, and a
 * row with no evidence is a row the card does not draw. That is the same *hidden, never blank*
 * discipline the reason list takes.
 */
export function evidenceOf<K extends Evidence['kind']>(
  candidate: Candidate,
  kind: K,
): Extract<Evidence, { readonly kind: K }> | undefined {
  const row = candidate.terms.find((term) => term.evidence.kind === kind);
  return row?.evidence as Extract<Evidence, { readonly kind: K }> | undefined;
}

/** The three facts the level row states, exactly as `player_card` published them. */
function levelFactsOf(candidate: Candidate): LevelRowFacts {
  const { level, band, range } = candidate.card;
  return { level, band, range };
}

/**
 * What the meta line states, or nothing at all.
 *
 * `distanceKm` is **omitted rather than zero** where the distance term stood down, and a meta
 * line with no distance in it would be an area comparison standing alone — which is the one
 * thing §6.3 licenses the client to compute and not a line the card was asked for. Hidden
 * rather than blank, once more.
 */
function metaFactsOf(candidate: Candidate, envelope: SearchEnvelope): MetaLineFacts | undefined {
  if (candidate.distanceKm === undefined) return undefined;
  return {
    km: candidate.distanceKm,
    theirAreaCode: candidate.card.areaCode,
    myAreaCode: envelope.myAreaCode,
  };
}

/**
 * The lines this surface says under the fit pill, in the order it draws them.
 *
 * `drawn` is the card's **own** exported set, passed in rather than looked up here: the set is
 * a statement about what that component draws, and this is not that component.
 *
 * **All three cards draw the whole selection, and the cap is `REASON_CAP`'s alone.** What the
 * social and deck cards *gain* is the reason line as a slot — without it `INTENT_ALIGNMENT`,
 * third-largest term in both modes, is invisible on two cards of three
 * ([`the-words.md`](../../../../../../docs/specs/matchmaking/the-words.md) §5) — not a second,
 * smaller cap of their own. A per-card count would be a fourth number nothing argues for, and
 * it would put the spoken name out of step with the drawing: §20.3 composes the card body's
 * label from these same lines, so a card drawing fewer than it announces is a card that says
 * one thing to a listener and another to a reader.
 */
function reasonLinesOf(candidate: Candidate, drawn: readonly Term[]): readonly string[] {
  return spoken(
    selectReasons({
      drawn,
      terms: candidate.terms,
      concerns: candidate.concerns,
      livenessReasons: candidate.livenessReasons,
      saysSomething: (term) => reasonLine(term.evidence) !== undefined,
    }),
  );
}

/** The selection, as the sentences it names. `hidden` is no line rather than an empty one. */
function spoken(selection: ReasonSelection): readonly string[] {
  switch (selection.kind) {
    case 'terms':
      // `saysSomething` already dropped every row this can decline for, so nothing is lost
      // here — the filter is what keeps the promise of three from printing two.
      return selection.terms.flatMap((term) => reasonLine(term.evidence) ?? []);
    case 'liveness':
      return [livenessLine(selection.reason)];
    case 'hidden':
      return [];
  }
}

/** The one concern a card draws, as a sentence. All of them are the why-fit sheet's. */
function concernLinesOf(candidate: Candidate): readonly string[] {
  return selectConcern({
    terms: candidate.terms,
    concerns: candidate.concerns,
    saysSomething: (term) => concernLine(term.evidence) !== undefined,
  }).flatMap((term) => concernLine(term.evidence) ?? []);
}
