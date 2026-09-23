/**
 * The verdict — one Skill rating as the result screen draws it, on one dark card.
 *
 * ```
 * YOUR LEVEL ⓘ                          ◯ 27%
 * 2,71                                   CONFIDENCE ⓘ
 * 2,09–3,33 likely range ⓘ
 * ────── the on-dark level bar, four band names, the legend ──────
 * Band                                        Established
 * Rating status                          Initial estimate
 * [Questions asked                                   12]
 * ```
 *
 * **A rating is never only a number.** The card leads with the Level, but shows it inside its
 * likely range, with its Confidence and its Band — two players both showing 3,0 at very
 * different Uncertainties are not the same player, and nothing here may imply they are.
 *
 * ## It is drawn twice, and it is one card
 *
 * The result screen draws it once, at the end of a rating run, for the rating that run
 * produced. **The Skill passport draws it once per rating** the player holds, unchanged, with
 * the sport tag and a status chip across its top
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2): a player who met their rating on this card recognises it when they come to look at it
 * again. So the card takes **a rating** — the fields both a finished run and a rating read back
 * carry — and two things only one caller has: the `top` slot, and the *Questions asked* row,
 * which is the run's own fact and is not drawn on the passport.
 *
 * ## The rules that are easy to break here
 *
 * - **Band boundaries come from the response.** They are deliberately uneven, they were
 *   wrong once already, and this client restates them nowhere. The level bar's own segment
 *   boundaries are drawing values and are never printed.
 * - **Confidence is drawn on the full 0–100 scale with the ceiling marked**, never rescaled
 *   so that a questionnaire's maximum fills the ring. The tick is what stops a short arc
 *   reading as failure — and **it is drawn only where a ceiling was served**, because a tick
 *   is a claim about what could have been proved and this client holds no copy of the number
 *   (7.8, as amended 2026-08-14).
 * - **Nothing on this card decides anything about the rating.** Every label and every figure
 *   is the server's, and the client renders them.
 *
 * ## The three marks, and where their popover lives
 *
 * None of the three figures is self-explanatory, so each carries an information mark. The
 * mark's popover anchors to the mark it was opened from and returns focus to it on close,
 * which is why the card holds its own three refs and hands the pressed one up: the **screen**
 * draws one popover — as a sibling of its root, never inside it — and a screen with several
 * cards draws one popover for all of them. The explainers' copy is the app's own, built per
 * rating because the one number in it is the served ceiling.
 */

import { useRef, useState, type MutableRefObject, type ReactNode } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { formatLevel, formatPercent, formatRange } from '@/shared/formatting/ratingFormat';
import {
  ConfidenceRing,
  DarkCard,
  Hairline,
  InfoMark,
  LevelBar,
  Popover,
  Row,
  theme,
  type FocusTarget,
} from '@/shared/ui';

import type { Band, LikelyRange } from '../domain/SkillRating';

import { BAND_NAMES, bandPresentation, ratingStatusLabel } from './bandPresentation';

export type ExplainerKey = 'level' | 'range' | 'confidence';

export interface Explainer {
  readonly title: string;
  readonly body: string;
}

/**
 * The three figures with an information mark, explained.
 *
 * This is the app's own copy, not the engine's — the wire carries no definition of what a
 * Level *is*. The one number in it is the ceiling, which the engine serves rather than the app
 * knowing, so the copy is built per rating instead of being a module constant: retuning the
 * ceiling moves this sentence with it and no release is involved.
 *
 * **With no ceiling served, the sentence naming one goes.** The rest still holds — what
 * Confidence is, and that matches are what raise it — but a rating whose ceiling this client
 * was not told has no number for "at most", and inventing one would state a limit nobody
 * served.
 */
export function explainers(ceiling: number | undefined): Readonly<Record<ExplainerKey, Explainer>> {
  return {
    level: {
      title: 'Your Level',
      body: 'Where you sit on the 1,00–5,00 scale for this sport. Your level changes as you play competitive matches.',
    },
    range: {
      title: 'Your likely range',
      body: 'Where Raketa thinks your level most likely sits, shown by the thin white bracket. A wider range means we are less certain about your level — not that you are weaker. As you play more, the range narrows and the confidence increases.',
    },
    confidence: {
      title: 'Confidence',
      body:
        ceiling === undefined
          ? 'Shows how confident Raketa is about your level, not how good you are. As you play more, Raketa learns and becomes more certain about your skill level.'
          : `Shows how confident Raketa is about your level, not how good you are. The questionnaire can provide up to ${ceiling}% confidence. As you play more, Raketa learns and becomes more certain about your skill level.`,
    },
  };
}

/** A mark that was pressed: which figure it explains, and the mark itself for the popover. */
export interface Explaining {
  readonly key: ExplainerKey;
  readonly trigger: FocusTarget;
}

/** Never just *Close* — 6.6's rule for every close control, which is that it says what it closes. */
export function explainerCloseLabel(explainer: Explainer): string {
  return `Close ${explainer.title}`;
}

/**
 * **Which mark the popover is open on, held past the close** — the state a screen drawing one
 * or more of these cards keeps, once, beside its one popover.
 *
 * Dropping the pressed mark the moment the popover closes would empty the card while it is
 * still fading out and — the part that matters — leave the close with no trigger to return
 * accessibility focus to. So the last mark is written during render rather than kept in a
 * second state that could disagree, and what the popover draws is the last one pressed
 * whether or not it is still open.
 *
 * @param ceiling the served ceiling the explainers are built against — a run's own, or none.
 */
export function useVerdictExplainer(ceiling: number | undefined) {
  const [explainer, setExplainer] = useState<Explaining>();
  const closing = useRef<Explaining>();
  if (explainer !== undefined) closing.current = explainer;
  const explaining = explainer ?? closing.current;

  return {
    /** Whether the popover is up — what the screen's root is hidden behind. */
    open: explainer !== undefined,
    /** Handed to every `Verdict` on the screen. */
    explain: setExplainer,
    popover: {
      visible: explainer !== undefined,
      trigger: explaining?.trigger,
      explained: explainers(ceiling)[explaining?.key ?? 'level'],
      onClose: () => setExplainer(undefined),
    },
  };
}

export type VerdictPopoverState = ReturnType<typeof useVerdictExplainer>['popover'];

/**
 * The one popover a screen draws for every card on it — **a sibling of the screen's root,
 * never a child**, because the root spreads `behindOverlay` while it is open and an overlay
 * inside that element would hide itself along with everything else.
 */
export function VerdictPopover({ visible, trigger, explained, onClose }: VerdictPopoverState) {
  return (
    <Popover
      visible={visible}
      trigger={trigger}
      title={explained.title}
      body={explained.body}
      closeLabel={explainerCloseLabel(explained)}
      onClose={onClose}
    />
  );
}

/** What the card draws — the fields a finished run and a rating read back both carry. */
export interface RatingVerdict {
  /** The Level. */
  readonly level: number;
  /** 0–100, on the full scale. */
  readonly confidence: number;
  /**
   * Where the ring's tick sits, or nothing. Served beside a run's result; **not served on a
   * rating read back**, which therefore draws no tick — see the module note.
   */
  readonly confidenceCeiling: number | undefined;
  readonly range: LikelyRange;
  readonly band: Band;
  /** Machine-readable; drawn through `ratingStatusLabel`. */
  readonly status: string;
}

export interface VerdictProps {
  readonly rating: RatingVerdict;
  /** Across the card's top, above the figures — the passport's sport tag and status chip. */
  readonly top?: ReactNode;
  /** The run's own row. Present on the result screen; absent on the passport. */
  readonly questionsAsked?: number;
  /** A mark was pressed. The screen opens its one popover on it. */
  readonly onExplain: (explaining: Explaining) => void;
}

/**
 * `MutableRefObject`, not the shared `FocusTarget`: the same ref is handed to `InfoMark` as a
 * *ref* and to `Popover` as a focus target, and `RefObject<View | null>` is covariant — it
 * will not go where a `Ref<View>` is wanted.
 */
type MarkRef = MutableRefObject<View | null>;

export function Verdict({ rating, top, questionsAsked, onExplain }: VerdictProps) {
  const band = bandPresentation(rating.band.name);
  const level = formatLevel(rating.level);
  const range = formatRange(rating.range);
  const confidence = formatPercent(rating.confidence);

  // One ref per mark, this card's own: the popover anchors to the mark it was opened from and
  // returns focus to it on close, which is one prop doing both jobs.
  const levelMark: MarkRef = useRef<View | null>(null);
  const rangeMark: MarkRef = useRef<View | null>(null);
  const confidenceMark: MarkRef = useRef<View | null>(null);

  return (
    <DarkCard>
      {top === undefined ? null : <View style={s.top}>{top}</View>}

      <View style={s.verdict}>
        <View style={s.figures}>
          <View style={s.figureHead}>
            <Text style={s.eyebrowOnDark}>Your level</Text>
            <InfoMark
              ref={levelMark}
              onDark
              onPress={() => onExplain({ key: 'level', trigger: levelMark })}
              accessibilityLabel="What your Level means"
            />
          </View>
          <Text style={s.level}>{level}</Text>

          <View style={s.figureHead}>
            <Text style={s.rangeValue}>{range}</Text>
            <Text style={s.rangeLabel}>likely range</Text>
            <InfoMark
              ref={rangeMark}
              onDark
              onPress={() => onExplain({ key: 'range', trigger: rangeMark })}
              accessibilityLabel="What your likely range means"
            />
          </View>
        </View>

        <View style={s.ring}>
          {/* The ceiling is the engine's and arrives with a run's result. Absent, the ring
              draws no tick and its name states the one number it has. */}
          <ConfidenceRing
            value={rating.confidence}
            ceiling={rating.confidenceCeiling}
            label="Confidence"
            accessibilityLabel={
              rating.confidenceCeiling === undefined
                ? `Confidence ${confidence}`
                : `Confidence ${confidence}, out of the ${rating.confidenceCeiling}% a questionnaire can prove`
            }
          />
          <InfoMark
            ref={confidenceMark}
            onDark
            onPress={() => onExplain({ key: 'confidence', trigger: confidenceMark })}
            accessibilityLabel="What Confidence means"
          />
        </View>
      </View>

      <View style={s.bar}>
        <LevelBar
          level={rating.level}
          range={rating.range}
          band={band?.key}
          bandNames={BAND_NAMES}
          variant="onDark"
          legend={{ mark: 'Your level', bracket: 'Likely range' }}
          accessibilityLabel={`Level ${level} of 5,00, likely range ${range}, band ${rating.band.name}`}
        />
      </View>

      <Hairline variant="onDark">
        <Row
          variant="onDark"
          label="Band"
          value={rating.band.name}
          accessibilityLabel={`Band: ${rating.band.name}`}
        />
        <Row
          variant="onDark"
          divided
          label="Rating status"
          value={ratingStatusLabel(rating.status)}
          accessibilityLabel={`Rating status: ${ratingStatusLabel(rating.status)}`}
        />
        {questionsAsked === undefined ? null : (
          <Row
            variant="onDark"
            divided
            label="Questions asked"
            value={String(questionsAsked)}
            accessibilityLabel={`Questions asked: ${questionsAsked}`}
          />
        )}
      </Hairline>
    </DarkCard>
  );
}

const s = StyleSheet.create({
  // The passport's tag and chip, one at each end, a step above the figures.
  top: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.space.sm,
  },
  verdict: { flexDirection: 'row', alignItems: 'center', gap: theme.space.md },
  figures: { flex: 1, gap: theme.space.xxs },
  figureHead: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  eyebrowOnDark: {
    ...theme.type.eyebrow,
    color: theme.color.onDarkEyebrow,
    textTransform: 'uppercase',
  },
  level: { ...theme.num.levelHero, ...theme.tabular, color: theme.color.surface },
  rangeValue: { ...theme.num.s, ...theme.tabular, color: theme.color.surface },
  rangeLabel: { ...theme.type.tiny, color: theme.color.onDarkTiny },
  ring: { alignItems: 'center', gap: theme.space.xxs },
  bar: { marginTop: theme.space.lg },
});
