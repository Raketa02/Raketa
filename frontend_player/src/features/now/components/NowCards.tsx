/**
 * The three card types, drawn.
 *
 * A match card is the **chip row** — the fit badge and one chip beside it — the
 * **status line**, the **reasons**, the spine, and, on a state card, the **action
 * row**.
 *
 * **A situation this build has never heard of draws the spine and drops the status
 * line.** It is never skipped: an app hiding a match the player has paid for is
 * the worst outcome on `ADR-0070`'s list and reads as *your app lost my booking*.
 * Losing the sentence loses exactly the thing that is actually missing, and the
 * mapper has already expressed that as `status === undefined`. The **action row is
 * unaffected**, because the act and `mayDepart` are spine facts: an unknown name
 * costs a phone one sentence and never the ability to take the seat.
 *
 * **Two card shapes, and `ADR-0088` says they are two.** The state card — the strip
 * and the offers region — reaches its act through a labelled button in the action
 * row. The **shelf** card reaches the same act through its **whole body** and gains
 * no button: a button roughly doubles a compact light-surface row, and `finishPaying`
 * overriding `takeSeat` is then one destination swap on one target rather than a
 * second control appearing. That inconsistency is the sharpest thing in `ADR-0088`
 * and is accepted there rather than papered over: the two were never the same
 * component and never looked alike.
 *
 * **A shelf card's body is a tap target exactly when the card names an act.** The
 * converse is `ADR-0083`'s — a card with no act has no button *and its body is not a
 * tap target either* — so an inert card is inert all the way through rather than a
 * control that swallows a press.
 *
 * **The shelf card's clock is a claim's clock and nothing else** (`ADR-0088`). The
 * card's own moment is the next thing that happens to a viewer *with a stake in the
 * match*, and a suggestion is a match she has none in; her own seat claim is about
 * her. When it is filled it **replaces** the tone tag rather than joining it: that
 * row is already two crowded groups, and while a player holds 1:30 to pay, *Forming*
 * is not the news.
 *
 * **The badge's second band is a colour and no word**, which is `ADR-0037` and `UI`
 * §B9's *"two bands only"*. What is added here is the **announced** state, because a
 * cue with no non-visual half is one nobody using assistive technology can have; the
 * drawing is untouched.
 *
 * A person and a club card have no situation half at all — three card types, not
 * one with holes — and neither is a tap target: shelf 4 is *"inert in v1 and styled
 * so"*, and shelf 5's tap into Find pre-filtered to that club is Find's own.
 */

import { StyleSheet, Text, View } from 'react-native';
import type { ReactNode } from 'react';

import { formatMoney } from '@/shared/lib/formatting';
import { Card, FitBadge, Note, PressableCard, Tag, theme } from '@/shared/ui';

import type { ClubCard, MatchCard, NowCard, PersonCard } from '../domain/ComposedScreen';
import type { FitBadge as FitBadgeValue } from '../domain/fitBadge';
import { FIT_UNSURE_WARNING } from '../mappers/fitReasons';

import { ActionRow, type CardControl } from './ActionRow';
import { CardClock } from './CardClock';
import { TONE_PRESENTATION } from './tonePresentation';
import { fitBadgeLabel } from './nowCopy';

/** The metadata separator, everywhere on this screen without exception. */
const SEP = ' · ';

/** One reason behind the badge, so *how many* is assertable rather than implied. */
export const FIT_REASON_ID = 'now-fit-reason';

/** The warning that stands in for a confidence number. Never a percentage. */
export const FIT_WARNING_ID = 'now-fit-warning';

/**
 * Whether the card fills the height of the row it sits in.
 *
 * Set by the two horizontal scrollers and by nothing else. `native-kit.md` §3
 * gives the action row `marginTop: auto` so footers align across cards of differing
 * height, and an auto margin needs a height to push against — which a card in a row
 * has and a card in a vertical column does not. `flex: 1` in a column whose own
 * height is content-driven collapses it, so this is deliberately not the default.
 */
export interface FillableCardProps {
  readonly fill?: boolean;
}

export interface NowCardViewProps extends FillableCardProps {
  readonly card: NowCard;
  readonly onControl: (control: CardControl) => void;
}

/** A shelf's card. It names no control; its **body** is the control, when it has one. */
export function NowCardView({ card, onControl, fill = false }: NowCardViewProps) {
  switch (card.kind) {
    case 'match':
      return <ShelfMatchCardView card={card} fill={fill} onControl={onControl} />;
    case 'person':
      return <PersonCardView card={card} />;
    case 'club':
      return <ClubCardView card={card} />;
  }
}

export interface MatchCardViewProps extends FillableCardProps {
  readonly card: MatchCard;
  readonly onControl: (control: CardControl) => void;
}

/** The state card: the strip and the offers region, with the action row. */
export function MatchCardView({ card, onControl, fill = false }: MatchCardViewProps) {
  return (
    <MatchCardShell card={card} fill={fill} chip={toneTag(card)}>
      <ActionRow card={card} onControl={onControl} />
    </MatchCardShell>
  );
}

function ShelfMatchCardView({
  card,
  fill,
  onControl,
}: {
  readonly card: MatchCard;
  readonly fill: boolean;
  readonly onControl: (control: CardControl) => void;
}) {
  // Bound to a `const` so the narrowing survives into the press handler, exactly as
  // the action row's does.
  const act = card.act;
  const claim = card.claimExpiresAt;

  return (
    <MatchCardShell
      card={card}
      fill={fill}
      // The claim replaces the tag; the card's own clock is not drawn here at all.
      chip={claim === undefined ? toneTag(card) : <CardClock moment={claim} />}
      press={
        act === undefined
          ? undefined
          : {
              // The code determined its own destination (`ADR-0083`); the body only
              // carries the press, and a screen holding a dozen of these needs the
              // announcement to say which club it is about.
              onPress: () => onControl({ kind: 'act', surface: act.surface, card }),
              accessibilityLabel: `${act.label}, ${card.where.clubName}`,
            }
      }
    />
  );
}

/**
 * What makes a card's body a control, or `undefined` for a card that is inert.
 *
 * **No hint.** The act's own label already names the act and its price, and the club
 * beside it names the match — a hint would be a third sentence restating the first.
 *
 * **A whole-card control is one accessibility element**, so a card that names an act
 * announces its label and nothing else: the badge, the reasons, the situation line
 * and the price all stop being reachable. That is a consequence of `ADR-0088`'s
 * *body rather than button* which the ADR does not discuss, and what a suggestion
 * card should announce as one element is copy design rather than an implementation
 * detail. Filed as `Raketa02/Raketa#116`, and unreachable until `#89` gives a shelf
 * card an act at all.
 */
interface CardPress {
  readonly onPress: () => void;
  readonly accessibilityLabel: string;
}

/**
 * The half both shapes share: the alert strip, the chip row, the status line, the
 * reasons and the spine.
 *
 * One body and two callers rather than one component with a shape flag — the flag
 * would be the sixth variant `ADR-0088` spent itself removing, one level up. What
 * the two callers differ in is what sits beside the badge, whether the body is a
 * control, and whether there is a footer at all.
 */
function MatchCardShell({
  card,
  fill,
  chip,
  press,
  children,
}: {
  readonly card: MatchCard;
  readonly fill: boolean;
  readonly chip: ReactNode | undefined;
  readonly press?: CardPress;
  readonly children?: ReactNode;
}) {
  const body = (
    <>
      <ChipRow card={card} chip={chip} />

      {card.status !== undefined ? <Text style={s.line}>{card.status.line}</Text> : null}

      {card.fit === undefined ? null : <FitReasons fit={card.fit} />}

      <Text style={s.meta}>
        {[card.where.clubName, card.where.cover, distance(card.where.distanceKm)]
          .filter((part): part is string => part !== undefined)
          .join(SEP)}
      </Text>

      <Text style={s.price}>{formatMoney(card.price)}</Text>

      {children}
    </>
  );

  return (
    <View style={[s.stack, fill ? s.fill : undefined]}>
      {card.status?.alert != null ? (
        // The strip above the card, on the three situations that leave a player
        // short of a player inside the rescue window.
        <Note variant="coral" accessibilityRole="alert">
          {card.status.alert}
        </Note>
      ) : null}

      {press === undefined ? (
        <Card style={[s.card, fill ? s.fill : undefined]}>{body}</Card>
      ) : (
        <PressableCard
          style={[s.card, fill ? s.fill : undefined]}
          onPress={press.onPress}
          accessibilityLabel={press.accessibilityLabel}
        >
          {body}
        </PressableCard>
      )}
    </View>
  );
}

/**
 * The badge and the one chip beside it.
 *
 * Absent entirely when neither is there, so a card that has no badge and no
 * nameable situation does not open with an empty row of its own height.
 */
function ChipRow({
  card,
  chip,
}: {
  readonly card: MatchCard;
  readonly chip: ReactNode | undefined;
}) {
  const fit = card.fit;
  if (fit === undefined && chip === undefined) return null;

  return (
    <View style={s.chips}>
      {fit === undefined ? null : (
        <FitBadge
          score={fit.score}
          // The composed screen's flag, read and never recomputed (`ADR-0037`).
          emphatic={card.emphasis}
          accessibilityLabel={fitBadgeLabel(fit.score, card.emphasis)}
        />
      )}
      {chip}
    </View>
  );
}

/**
 * The tone tag, or `undefined` for a situation this build cannot name.
 *
 * A function rather than a component, so that *there is no chip* is a value the
 * chip row can see. A component returning `null` is still an element to its caller,
 * and the row would open with an empty line of its own gap.
 */
function toneTag(card: MatchCard): ReactNode | undefined {
  const status = card.status;
  if (status === undefined) return undefined;

  const tone = TONE_PRESENTATION[status.tone];
  return <Tag label={status.tag} variant={tone.variant} dot={tone.dot} />;
}

/**
 * Why this one — up to three, and a warning where a percentage would be.
 *
 * **Never a number.** `ADR-0037`: coverage ranks the list and gates emphasis and
 * *"never becomes a second gauge on the card"*; what an uncertain estimate becomes
 * is words. The mark carries the state as a shape so the amber is not doing it
 * alone, and both marks are hidden from assistive technology, which is handed the
 * sentence instead.
 */
function FitReasons({ fit }: { readonly fit: FitBadgeValue }) {
  if (fit.reasons.length === 0 && !fit.unsure) return null;

  return (
    <View style={s.reasons}>
      {/* Keyed by position, which is the honest key here: the list is three
          sentences deep, never reorders, and is rebuilt whole from the wire on
          every compose. Keying by the sentence assumes two terms cannot word
          themselves the same way — an assumption the copy table can break in a
          single edit, and one whose failure is a silently dropped reason. */}
      {fit.reasons.map((reason, index) => (
        <View key={index} style={s.reason} testID={FIT_REASON_ID}>
          <Mark glyph="✓" colour={theme.color.mint} />
          <Text style={s.reasonLine}>{reason}</Text>
        </View>
      ))}

      {fit.unsure ? (
        <View style={s.reason} testID={FIT_WARNING_ID}>
          <Mark glyph="!" colour={theme.color.amber} />
          <Text style={s.warningLine}>{FIT_UNSURE_WARNING}</Text>
        </View>
      ) : null}
    </View>
  );
}

function Mark({ glyph, colour }: { readonly glyph: string; readonly colour: string }) {
  return (
    <Text
      style={[s.mark, { color: colour }]}
      accessibilityElementsHidden
      importantForAccessibility="no"
    >
      {glyph}
    </Text>
  );
}

function PersonCardView({ card }: { readonly card: PersonCard }) {
  return (
    <Card style={s.card}>
      <Text style={s.title}>{card.nickname}</Text>
    </Card>
  );
}

function ClubCardView({ card }: { readonly card: ClubCard }) {
  return (
    <Card style={s.card}>
      <Text style={s.title}>{card.name}</Text>
      {card.distanceKm !== undefined ? (
        <Text style={s.meta}>{distance(card.distanceKm)}</Text>
      ) : null}
    </Card>
  );
}

/** `2,4 km`. A comma decimal, like every other figure the shared table renders. */
function distance(km: number | undefined): string | undefined {
  if (km === undefined) return undefined;
  const tenths = Math.round(km * 10);
  return `${Math.trunc(tenths / 10)},${tenths % 10} km`;
}

const s = StyleSheet.create({
  stack: { gap: theme.space.xs },
  card: { gap: theme.space.xs },
  fill: { flex: 1 },
  chips: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  title: { ...theme.type.cardTitle, color: theme.color.ink },
  line: { ...theme.type.tiny, color: theme.color.ink },
  reasons: { gap: theme.space.xxs },
  reason: { flexDirection: 'row', alignItems: 'flex-start', gap: theme.space.xs },
  mark: { ...theme.type.tag },
  reasonLine: { ...theme.type.tiny, color: theme.color.ink, flex: 1 },
  warningLine: { ...theme.type.tiny, color: theme.color.amber, flex: 1 },
  meta: { ...theme.type.tiny, color: theme.color.muted },
  price: { ...theme.num.s, ...theme.tabular, color: theme.color.ink },
});
