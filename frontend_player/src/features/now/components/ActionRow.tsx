/**
 * The action row: three optional slots, zero variants.
 *
 * `ADR-0088`, which is the authority for every line below. Three decisions in three
 * days had pulled this row into five shapes and none of them owned it; the answer
 * to *how many variants may the client hold* is **none**. One row, and each slot
 * appears exactly when its own field is present.
 *
 * | Slot | Present when | Drawn as |
 * | --- | --- | --- |
 * | **Clock** | the card's one clock slot holds a moment | mono, leftmost, never shrinks |
 * | **Act** | the spine carries an act code | the primary button at `flex: 1` |
 * | **Exit** | `mayDepart` | the stock outline glyph, 44 × 44 reachable, rightmost |
 *
 * **Vacant slots do not stretch.** The act is the only flexible element: with no
 * act the clock stays left and the exit stays right, and nothing grows to fill the
 * gap, because a stretched icon reads as a primary button that has forgotten its
 * label.
 *
 * **The empty row still renders**, as a zero-height spacer. `native-kit.md` §3
 * gives the row `marginTop: auto` so footers align across cards of differing
 * height and short cards stop floating in a *"slab of empty night"* — and an
 * element that is not rendered pushes nothing, so the twenty-six cards that name
 * no act would get the slab back.
 *
 * **Neither of the prototype's two icons is here.** `✉` duplicated a tab-bar
 * button once per card, and `⌘` opened a sheet showing four dots everywhere it
 * survived — on the one card where that sheet has something to say, `ready`, its
 * primary button already goes there. `ADR-0088` records dropping them as a genuine
 * override of a UI authority rather than as a forced consequence, and
 * `nowDiscipline.test.ts` walks the feature so neither comes back.
 *
 * **The exit is not the loudest thing on the card.** Now is a screen about
 * reassurance; the control that ends a game is a muted glyph beside a coloured
 * button, and past the point of departure it is **absent rather than refusing** —
 * which is the server's boolean and never something the phone works out.
 */

import { Feather } from '@expo/vector-icons';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Button, theme } from '@/shared/ui';

import type { MatchCard, Moment } from '../domain/ComposedScreen';
import type { ActSurface } from '../domain/presentation';
import { countdownLabel, remainingMs } from '../domain/countdown';

import { useNowClock } from './NowClock';
import { clockAccessibilityLabel, exitLabel, EXIT_HINT } from './nowCopy';

/**
 * What a press on a card's own controls means.
 *
 * One shape rather than two callbacks, so a region threads one prop and the screen
 * answers in one place. The exit is **not** an act code — `ADR-0086` refuses to
 * reopen the enumeration `ADR-0083` closed for something that is not the card's
 * act — so it is its own kind here rather than a seventh surface.
 */
export type CardControl =
  | { readonly kind: 'act'; readonly surface: ActSurface; readonly card: MatchCard }
  | { readonly kind: 'exit'; readonly card: MatchCard };

export const ACTION_ROW_ID = 'now-card-action-row';
export const CLOCK_ID = 'now-card-clock';

export interface ActionRowProps {
  readonly card: MatchCard;
  readonly onControl: (control: CardControl) => void;
}

export function ActionRow({ card, onControl }: ActionRowProps) {
  const moment = clockMoment(card);
  // Bound to a `const` so the narrowing survives into the press handler. The
  // alternative is re-reading `card.act` inside a closure, which TypeScript
  // cannot narrow — and which would need a runtime refusal for a case the JSX
  // above has already excluded.
  const act = card.act;

  return (
    <View testID={ACTION_ROW_ID} style={s.row}>
      {moment === undefined ? null : <CardClock moment={moment} />}

      {act === undefined ? null : (
        <Button
          label={act.label}
          // A screen holds a dozen of these. The visible label is the same on
          // every card offering the same act, so the announced one names the club
          // it is about — which is what `Button` keeps this prop for.
          accessibilityLabel={`${act.label}, ${card.where.clubName}`}
          // The code determined its own destination (`ADR-0083`); this only reads
          // it, and the card beside it says what the destination is about.
          onPress={() => onControl({ kind: 'act', surface: act.surface, card })}
          style={s.act}
        />
      )}

      {card.mayDepart ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={exitLabel(card.where.clubName)}
          accessibilityHint={EXIT_HINT}
          accessibilityState={{ disabled: false }}
          hitSlop={theme.hit.btn}
          onPress={() => onControl({ kind: 'exit', card })}
          style={({ pressed }) => [s.exit, pressed ? s.exitPressed : undefined]}
        >
          <Feather
            name="log-out"
            size={theme.size.tabIcon}
            color={theme.color.muted}
            // The label on the control beside it already says what this is.
            accessibilityElementsHidden
            importantForAccessibility="no"
          />
        </Pressable>
      ) : null}
    </View>
  );
}

/**
 * Which of the card's two moments fills its one slot.
 *
 * **A live seat claim wins.** `ADR-0081` worried about exactly the alternative —
 * *"a card counting 1:30 to pay under a button offering anything else is two
 * instructions"* — and `ADR-0088` settles it: the claim's five minutes override the
 * card's clock. `Raketa02/Raketa#86` left the choice here deliberately, because
 * *which* of the two can run out is not a choice at all and the fourth ask already
 * watches both.
 *
 * This is not a rule the phone holds. Both moments were sent; picking which of the
 * two the one slot draws is where a control sits, which is the client's half of the
 * line `ADR-0088` draws.
 */
function clockMoment(card: MatchCard): Moment | undefined {
  return card.claimExpiresAt ?? card.clock;
}

/**
 * The countdown, repainted by the screen's one clock.
 *
 * Its own component so that a tick re-renders the figures and nothing else — a
 * card whose clock is empty does not read the context at all.
 *
 * **`flexShrink: 0` and a floor on the width.** `ADR-0088` makes the act the only
 * flexible element; a countdown that shrank under a long label would be the one
 * element on the card that changes size as the seconds fall.
 */
function CardClock({ moment }: { readonly moment: Moment }) {
  const now = useNowClock();
  if (now === undefined) return null;

  const left = remainingMs(moment, now);
  // A moment that does not parse is a contract failure rather than a state, and
  // the answer is *there is no countdown here* rather than a figure in decades.
  if (left === undefined) return null;

  const label = countdownLabel(left);

  return (
    <Text
      style={s.clock}
      numberOfLines={1}
      accessibilityLabel={clockAccessibilityLabel(label)}
      testID={CLOCK_ID}
    >
      {label}
    </Text>
  );
}

const s = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    // Footers align across cards of differing height, per `native-kit.md` §3. On a
    // card that is its own height this is worth nothing and costs nothing.
    marginTop: 'auto',
  },
  clock: {
    ...theme.num.xs,
    ...theme.tabular,
    color: theme.color.ink,
    flexShrink: 0,
    minWidth: theme.size.timeSquare,
  },
  // The only flexible element in the row.
  act: { flex: 1 },
  exit: {
    width: theme.size.minTouch,
    height: theme.size.btn,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: theme.radius.btn,
  },
  exitPressed: { backgroundColor: theme.color.line2 },
});
