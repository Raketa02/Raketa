/**
 * **`SH.whyfit`** — the whole Fit calculation, and the one surface allowed to draw a term row.
 *
 * One component taking `(candidate, envelope)` and reading **no global state**, which is what
 * lets it name no mode on the deck: `SearchEnvelope.mode` is null exactly there, and deriving
 * a vector from the declared intent would be the engine's own resolution rule rewritten in
 * TypeScript ([#233](https://github.com/Raketa02/Raketa/issues/233) §6). One sheet, three
 * entry points, one input.
 *
 * ## Five zones, and the row count is derived
 *
 * 1. **Term rows** — every term that *fired*, uncapped, in the order they arrived, which is
 *    ranked by contribution. **4 to 7 today, varying per candidate on the same screen**: only
 *    `LEVEL_FIT` and `DISTANCE` never stand down, and day one `RELIABILITY` stands down for
 *    everybody. The prototype's seven and today's seven are the same number for unrelated
 *    reasons, and reading the second as the first is how this sheet was drawn wrong.
 * 2. **The sub-total**, because `fit` is *not* what the terms sum to: `fit = Σcontributions +
 *    applied`, so the step from the rows to the number in the pill is visibly the modifier
 *    block rather than an unexplained gap.
 * 3. **The modifiers**, headed by the derived `applied`.
 * 4. **What else moved you here** — the liveness reasons and the inclusion reason. A card
 *    shows at most one; this is where the rest live.
 * 5. **The footer** — the platform's own gap, stated once, and the two version stamps.
 *
 * **The not-counted block sits between 2 and 3, and that is argued rather than convenient.**
 * `the-play-screens.md` §8 puts it *"beneath the rows"*, and #273's AC-2 lists the five zones
 * as *term rows → sub-total → modifiers*, so one adjacency has to give. #233 §3 decides which:
 * the sheet prints a sub-total *"where the terms stop, and the step from there to `✦ {score}`
 * is **visibly the modifier block** rather than an unexplained gap"* — an argument about those
 * two being read together. So the block goes beneath the rows **and their total**, beside the
 * basis line that explains why the weights are the weights, and the arithmetic runs unbroken
 * from the sub-total to the number in the pill.
 *
 * ## A stood-down term is not a term row
 *
 * It has no weight, no value, no contribution and no evidence — four of a row's five cells —
 * so drawing it greyed invents the shape of a reading that does not exist. The live terms are
 * rows; the rest are a **list**, each line pairing the term with whose gap it was, because
 * `INTENT_ALIGNMENT + NOTHING_FROM_THEM` and `SOCIAL_VIBE + NOTHING_FROM_THEM` are two
 * different sentences from one code.
 *
 * **Two tiers, and the platform's own is stated once.** `NOT_YET_ON_THIS_PLATFORM` is a fact
 * about the platform rather than about these two people, so it is the footer's; drawing it
 * per row would print reliability's line identically on twenty cards and read as twenty
 * separate shortfalls.
 *
 * ## Concerns are marked in place, never gathered
 *
 * `concerns` reads scored terms only — *a term that stood down is not a concern* — so every
 * concern's term is **guaranteed** to be a row already drawn with its meter, and a summary
 * block would restate a value this sheet has just rendered, which is §10's rule broken on the
 * one screen whose job is showing values. *"Why 78? shows all of them"* stays true: all of
 * them are shown, each on its own row. The trade, named: a concerned term with a low
 * contribution sits at the bottom, so the warning is where the arithmetic put it rather than
 * where attention is.
 *
 * ## The meter is decoration and the row's words carry it
 *
 * The row draws a label, a mono `×{weight} → {contribution}`, **then** a meter. The number is
 * already text two words earlier, so the meter is hidden from assistive technology and takes
 * no label at all — 6.8's argument about its column heads, and the reason `progressbar`
 * appears nowhere in this contract (§20.8).
 *
 * ## And it explains the number beside the face, never the seating
 *
 * On a court seat the breakdown in `candidates[]` is the **pairwise** Fit, while what put that
 * person in that seat is the group objective — recorded and never returned as a number,
 * reaching the client only as a `GroupReason`. This sheet explains the Fit honestly and
 * completely and says nothing about seating: a line acknowledging the four would invite it to
 * explain a second score the player is never shown.
 */

import { StyleSheet, Text, View } from 'react-native';

import { OUT_OF_DATE_GAP, orOutOfDate } from '@/shared/vocabulary/outOfDate';
import { BottomSheet, Hairline, Meter, Row, theme, type FocusTarget } from '@/shared/ui';

import type { Candidate, SearchEnvelope } from '../../domain/candidate';
import { whyFitColumn } from '../../domain/whyFitColumn';
import { whyFitRowLabel, whyFitSheetLabel } from '../accessibilityPresentation';
import { concernLine } from '../concernPresentation';
import { NOT_ON_THIS_PLATFORM_FOOTER, degradedLine } from '../degradedPresentation';
import { WHAT_ELSE_MOVED_YOU_HERE, inclusionLine, livenessLine } from '../livenessPresentation';
import {
  MODIFIERS_HEADING,
  TERM_SUBTOTAL_LABEL,
  adjustmentsTotal,
  modifierLine,
} from '../modifierPresentation';
import { reasonLine } from '../reasonPresentation';
import { whyFitHeader } from '../searchingPresentation';
import { termLabel } from '../termPresentation';
import {
  NOT_COUNTED_HEADING,
  WEIGHT_BASIS,
  signedFigure,
  termFigure,
  versionStamp,
  whyFitCloseLabel,
  whyFitTitle,
} from '../whyFitPresentation';

export interface WhyFitSheetProps {
  readonly visible: boolean;
  readonly onClose: () => void;
  readonly candidate: Candidate;
  readonly envelope: SearchEnvelope;
  /** The name the surface already drew — §15's whole handle, never re-derived here. */
  readonly name: string;
  /** The control the sheet was opened from. Focus returns there on close. */
  readonly returnFocusTo?: FocusTarget;
}

export function WhyFitSheet({
  visible,
  onClose,
  candidate,
  envelope,
  name,
  returnFocusTo,
}: WhyFitSheetProps) {
  const column = whyFitColumn(candidate);
  const concerned = new Set(candidate.concerns);

  // The platform's own gap is the footer's, and the per-person gaps are the block's. Split
  // here rather than at each draw site, so *stated once* is arithmetic instead of a rule.
  const platformGap = candidate.degradedTerms.some(
    (degraded) => degraded.reason === 'NOT_YET_ON_THIS_PLATFORM',
  );
  const personGaps = candidate.degradedTerms.filter(
    (degraded) => degraded.reason !== 'NOT_YET_ON_THIS_PLATFORM',
  );

  const adjusted = candidate.modifiers.length > 0 || column.applied !== 0;

  return (
    <BottomSheet
      visible={visible}
      onClose={onClose}
      title={whyFitTitle(column.fit)}
      closeLabel={whyFitCloseLabel(name)}
      returnFocusTo={returnFocusTo}
    >
      {/* The sheet's accessible name, which is deliberately not its visible title: the ✦
          must not be spoken (§20.6). The heading `BottomSheet` focuses carries the visible
          one, so this is the sheet as a whole. */}
      <View accessible accessibilityLabel={whyFitSheetLabel(column.fit)}>
        <Text style={s.header}>
          {whyFitHeader({ liveTerms: column.rows.length, mode: envelope.mode })}
        </Text>
      </View>

      {column.rows.map((row, at) => {
        const figure = termFigure(row);
        // ADR-0106 §6 lands **in place**: an unknown `Term` takes the whole row's label, and
        // the numbers beside it stand — *"those are numbers, not codes"*.
        const label = orOutOfDate(row.term.term === null ? undefined : termLabel(row.term.term));
        const isConcern = row.term.term !== null && concerned.has(row.term.term);
        // A concern is the engine's own graded claim about a term, and it replaces the reason
        // line on the row rather than being added under it: one term saying "✓ X" and "! X"
        // is §10's rule broken at its own root. An evidence variant this build has no
        // renderer for puts the gap where the reason line goes. The candidate goes with the
        // evidence: the distance sentence prints its one-decimal `distanceKm` — the number
        // the card printed — and never the whole kilometres the engine scored.
        const said =
          row.term.evidence === null
            ? OUT_OF_DATE_GAP
            : isConcern
              ? concernLine(row.term.evidence)
              : reasonLine(row.term.evidence, candidate);

        return (
          <View
            // The term where there is one, and the position where there is not: two rows this
            // build cannot name are two rows, and a key of `null` would collapse them.
            key={row.term.term ?? `unreadable-${at}`}
            style={s.term}
            accessible
            accessibilityLabel={whyFitRowLabel({
              term: label,
              figure,
              ...(said === undefined ? {} : { reason: said }),
            })}
          >
            <Row label={label} value={<Text style={s.figure}>{figure}</Text>} />
            <Meter share={row.term.value} />
            {said === undefined ? null : (
              <Text style={isConcern ? s.concern : s.reason}>{said}</Text>
            )}
          </View>
        );
      })}

      {/* The fold is a wrapper around the section below it (5.3), which is what keeps the
          spacing on both sides of the line from being written twice. */}
      <Hairline>
        <Row label={TERM_SUBTOTAL_LABEL} value={<Text style={s.figure}>{column.subtotal}</Text>} />
        <Text style={s.basis}>{WEIGHT_BASIS}</Text>
      </Hairline>

      {personGaps.length === 0 ? null : (
        <View style={s.block}>
          <Text style={s.heading}>{NOT_COUNTED_HEADING}</Text>
          {personGaps.map((degraded, at) => (
            <Text key={degraded.term ?? `unreadable-${at}`} style={s.line}>
              {/* A term or a reason this build cannot read takes the gap **in place**: the
                  block is the renormalisation basis, and a line that vanished would make it
                  silently shorter than the answer it describes (§3). */}
              {orOutOfDate(
                degraded.term === null || degraded.reason === null
                  ? undefined
                  : degradedLine(degraded.term, degraded.reason),
              )}
            </Text>
          ))}
        </View>
      )}

      {!adjusted ? null : (
        <View style={s.block}>
          <Text style={s.heading}>{MODIFIERS_HEADING}</Text>
          <Text style={s.line}>{adjustmentsTotal(signedFigure(column.applied))}</Text>
          {/* One row per adjustment, and **nothing sums them**: the rows carry pre-budget
              entry points and the only total anybody may read is the derived one above. */}
          {candidate.modifiers.map((modifier) => (
            <Row
              key={modifier.code}
              label={modifierLine(modifier.code)}
              value={<Text style={s.figure}>{signedFigure(modifier.points)}</Text>}
            />
          ))}
        </View>
      )}

      {candidate.livenessReasons.length === 0 && candidate.inclusionReason === undefined ? null : (
        <View style={s.block}>
          <Text style={s.heading}>{WHAT_ELSE_MOVED_YOU_HERE}</Text>
          {candidate.inclusionReason === undefined ? null : (
            <Text style={s.line}>{inclusionLine(candidate.inclusionReason)}</Text>
          )}
          {candidate.livenessReasons.map((reason) => (
            <Text key={reason} style={s.line}>
              {livenessLine(reason)}
            </Text>
          ))}
        </View>
      )}

      <Hairline style={s.footer}>
        {/* Stated once, and only where something actually stood down for it. It names no term
            and no person: what it reports is that the platform is not finished. */}
        {platformGap ? <Text style={s.line}>{NOT_ON_THIS_PLATFORM_FOOTER}</Text> : null}
        <Text style={s.versions}>{versionStamp(envelope)}</Text>
      </Hairline>
    </BottomSheet>
  );
}

const s = StyleSheet.create({
  header: { ...theme.type.tiny, color: theme.color.muted },
  term: { paddingTop: theme.space.xs, gap: theme.space.xxs },
  figure: { ...theme.num.xs, color: theme.color.ink },
  reason: { ...theme.type.tiny, color: theme.color.muted },
  concern: { ...theme.type.tiny, color: theme.color.amber },
  basis: { ...theme.type.tiny, color: theme.color.muted, paddingTop: theme.space.xs },
  block: { paddingTop: theme.space.sm, gap: theme.space.xxs },
  heading: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  line: { ...theme.type.tiny, color: theme.color.ink },
  footer: { gap: theme.space.xxs },
  versions: { ...theme.num.xs, color: theme.color.muted },
});
