/**
 * **The pool's header** — the court being filled, drawn on the screen that fills it
 * ([#299](https://github.com/Raketa02/Raketa/issues/299)).
 *
 * *Pick players* is a long ranked list, and the one thing a player could not see while working
 * down it was the thing they were picking **into**. This is that: a small court that gains a
 * face on every add, what the four are worth so far, and the way back to the court itself.
 *
 * The surface is not new. `the-play-components.md` §5 licenses the 46pt seat label's truncation
 * on the grounds that *"both screens the court appears on already print the names in full and
 * unavoidably"* — the forecast card's figures row, and **this** header's names line, which had
 * never been built. 7.11 built `BalanceBar`'s `onDark` variant for *"the pool header draws this
 * bar inside a dark card"*, against a card that did not exist either. Both are discharged here.
 *
 * ## It replaces the forecast card rather than standing above it
 *
 * The pool drew *How it sits so far* as a plain `Card`: a heading, the tinted figure, the
 * balance word, the assumption. Every one of those facts is in this card, and a second one
 * restating them is the screen saying one thing twice. `POOL_FORECAST_HEADING` goes with it — a
 * card whose first row is a drawn court does not need a heading explaining that it is about the
 * court.
 *
 * **The assumption does not go with it.** ADR-0108's rule is that the figure and its caveat are
 * one thing, so it moves under the reading, where the three-of-four state is exactly what it is
 * for.
 *
 * ## What the bottom half says is a question about the far side, not about fullness
 *
 * The engine serves a forecast from the first person added and reaches it by assuming an empty
 * seat matches the player opposite, so a figure over a one-sided court is the assumption
 * talking rather than a reading of a game (`theirSideSeated`). Until somebody is across the
 * net the card says the act that would produce one; after, it draws the split and the bar, with
 * the engine's own caveat under them while a seat is still open.
 *
 * ## What is composed, what is hidden, and what is simply a sentence
 *
 * §20.1: one element per action, everything actionless merging into the nearest action above
 * it. Two blocks here are **composed** rather than left as their parts. The court, the count
 * and the names are one element (`poolHeaderLabel`) — a listener navigating a drawn court,
 * then a count, then four names stops three times to assemble one claim — and the split row is
 * another (`splitRowLabel`), for the same reason about five figures. The *Court* control is the
 * only action on the card.
 *
 * Two things are drawn and hidden: `CourtMini`'s own summary, because the element around it
 * already carries that sentence, and the bar, because the row above it prints all three of its
 * numbers, which is the builder's reason for hiding its own.
 *
 * **The caveat under the reading is left as an ordinary `Text`, and that is not an oversight.**
 * A `Text` is an accessibility element in React Native, so the card is not *three* elements —
 * it is the two composed blocks, the control, and whichever sentence is drawn. §20.1's merge
 * rule is about parts of one claim being navigated separately; a caveat is its own sentence
 * and reads as one, exactly as the assumption did on the card this replaces.
 *
 * ## The figure is white, and the tint is the one thing that did not survive the dark card
 *
 * `BALANCE_INK` is **paper ink**: `mintInk`, `amber` and `red` measure 2,28 / 2,33 / 2,25 : 1
 * against `night`, which Part 13 permits at no size — the same defect Part 16 recorded for
 * 7.5's band inks on 2026-08-14. It read as legible on the `Card` this replaces because that
 * card was white.
 *
 * So the figure takes 5.2's own repaint, which for text on a dark card is **white** and never a
 * second chromatic scheme, and the reading is carried by `balanceWord` beside it — which Part
 * 13 required there anyway, since colour is never the only signal. Nothing is lost that was
 * being read: a tint at 2,3 : 1 was not communicating a tone to anybody.
 *
 * A legible on-dark tone set is a design-system extension (15.2, three measured values) rather
 * than three hexes invented at a call site, and it is filed as one.
 *
 * ## No live region here
 *
 * §20.9's third region announces the provisional figure, and it stays the **builder's**: that
 * screen is still mounted underneath this route and already holds it, and `announce` is
 * imperative, so claiming it here would say one change twice. The figure moving into a header
 * does not move the region with it.
 */

import { StyleSheet, Text, View } from 'react-native';

import { formatLevel, formatPercent } from '@/shared/formatting/ratingFormat';
import { handleStem } from '@/shared/formatting/playerName';
import {
  BalanceBar,
  BalanceBarTone,
  Button,
  DarkCard,
  Hairline,
  theme,
  type SportKey,
} from '@/shared/ui';

import type { Candidate } from '../domain/candidate';
import type { Arrangement, Seating } from '../domain/forecast';
import { seatsFilled, theirSideSeated, toBuildSeat } from '../domain/forecast';
import { seatPlaces } from '../domain/lineup';

import { courtSummaryLabel, poolHeaderLabel, splitRowLabel } from './accessibilityPresentation';
import { balanceLabel, balanceTone } from './balancePresentation';
import { GAP_WORD, SIDE_HEADINGS, sideName } from './builderPresentation';
import { CourtMini } from './court/CourtMini';
import type { CourtFaceOccupant } from './court/seatFace';
import { handlesOn } from './court/seatedHandles';
import { POOL_COURT_LABEL, poolSeatedLine } from './poolPresentation';

export interface PoolHeaderProps {
  readonly sport: SportKey;
  /** This app's word for that sport. The court's caption uppercases it itself. */
  readonly sportName: string;
  readonly seats: number;
  /** Who is where, as the screen already derived it through `seatingToDraw`. */
  readonly seated: Seating;
  /** The rows the record still holds, for the names and the faces. */
  readonly rows: ReadonlyMap<string, Candidate>;
  /** Your own player id — the account's. Absent for the frame the launch read is in flight. */
  readonly self: string | undefined;
  /**
   * The arrangement being read, where one has landed.
   *
   * Absent is *no forecast yet*, which is not the same state as *nobody across the net*: both
   * draw the sentence, and only the second one is a thing the player can act on. The card does
   * not tell them apart, because the act it offers is the right one either way.
   */
  readonly arrangement?: Arrangement;
  /** Back to the court. The pool was pushed over it, so this pops. */
  readonly onCourt: () => void;
}

export function PoolHeader({
  sport,
  sportName,
  seats,
  seated,
  rows,
  self,
  arrangement,
  onCourt,
}: PoolHeaderProps) {
  const filled = seatsFilled(seated);
  const places = seatPlaces(seated.map(toBuildSeat));

  const yours = handlesOn('yours', seated, places, { rows, self });
  const theirs = handlesOn('theirs', seated, places, { rows, self });
  /** Your side first, which is the order the court hands its seats and the names are read in. */
  const names = [...yours, ...theirs].map((one) => one.name);

  /**
   * The reading, or nothing — **gated on the far side rather than on a full court**.
   *
   * Both halves of the condition are real states: a forecast that has not landed, and a court
   * whose far half is empty. See the module note.
   */
  const read = arrangement !== undefined && theirSideSeated(seated) ? arrangement : undefined;
  const tone = read === undefined ? undefined : balanceTone(read.forecast.pct);

  return (
    <DarkCard style={s.card}>
      <View style={s.top}>
        {/* One element over three actionless things — §20.1's merge rule. */}
        <View
          style={s.claim}
          accessible
          accessibilityLabel={poolHeaderLabel({
            sportName,
            filled,
            seats,
            names,
            ...(read === undefined ? {} : { pct: read.forecast.pct }),
          })}
        >
          {/* Hidden: the element around it already says the sentence `Court` would announce,
              and the Sport under the picture is the first word of that sentence.

              **The Sport is under the court and no longer on it.** 7.12's caption is a band
              inside the drawing, over a gradient, and at `size.court.header` it lands across
              the near baseline of a court that now has four faces on it. Out here it is the
              same eyebrow, centred on the same width, with the picture left to be a picture —
              and the shadow goes with the band, because there is no image behind it to
              separate the word from. */}
          <View
            style={s.court}
            accessibilityElementsHidden
            importantForAccessibility="no-hide-descendants"
          >
            <CourtMini
              sport={sport}
              width={theme.size.court.header}
              summary={courtSummaryLabel({ sportName, filled, seats })}
              seats={seated.map((seat) => faceOf(seat, { rows, self }))}
            />
            <Text style={s.sport}>{sportName}</Text>
          </View>

          {/* The count alone. **The handles are in the band**, on the two segment labels, and
              printing them here as well would be the same four names twice in one card — which
              is why the line that used to sit under this one is gone. They are still whole in
              the spoken name, where nothing else carries them. */}
          <View style={s.who}>
            <Text style={s.count}>{poolSeatedLine({ filled, seats })}</Text>
          </View>

          {/* The figure and nothing under it. §B9's balance word stood here while the figure
              was **tinted** — Part 13's *never colour alone*, where the word said what the
              colour meant. The figure is white now (see the module note), so there is no
              colour to read and no word owed: what is left is a number, on the axis the
              control beside it sits on. The word is still the whole of the bar's own spoken
              name, and of this block's. */}
          {read === undefined ? null : (
            <Text style={s.figure}>{formatPercent(read.forecast.pct)}</Text>
          )}
        </View>

        <Button label={POOL_COURT_LABEL} variant="onDark" size="sm" onPress={onCourt} />
      </View>

      {/* **The reading, or nothing at all.** A sentence stood here promising the figure that
          would appear once somebody was across the net — *Add somebody to their side and a
          running balance appears here.* It is gone: the act it described is the whole of what
          this screen is for and the list beneath is already offering it, so the line was a
          caption on an absence, printed under a court whose own empty seats say the same
          thing. The rule the header keeps is the one it always had — the block is drawn when
          there is a reading and not drawn when there is not, which is the *hidden, never
          blank* discipline every absence on these screens takes. */}
      {read === undefined || tone === undefined ? null : (
        <Hairline variant="onDark">
          <Reading arrangement={read} tone={tone} sides={{ yours, theirs }} />
        </Hairline>
      )}
    </DarkCard>
  );
}

/**
 * The split, the bar, and the caveat under both — **every figure read, none computed**.
 *
 * All three numbers are `split`'s: a side's strength is not the mean of the people standing on
 * it, so the one honest way to draw this row was for the engine to serve it (#289, ADR-0136),
 * and §11.3's check is looking for arithmetic. There is none here.
 */
function Reading({
  arrangement,
  tone,
  sides,
}: {
  readonly arrangement: Arrangement;
  readonly tone: BalanceBarTone;
  readonly sides: {
    readonly yours: readonly { readonly name: string }[];
    readonly theirs: readonly { readonly name: string }[];
  };
}) {
  const { split, forecast } = arrangement;

  /** Whole handles for the sentence a listener hears; stems for the boxes a reader sees. */
  const spoken = {
    yours: sideName(
      sides.yours.map((one) => one.name),
      SIDE_HEADINGS.yours,
    ),
    theirs: sideName(
      sides.theirs.map((one) => one.name),
      SIDE_HEADINGS.theirs,
    ),
  };
  const drawn = {
    yours: sideName(
      sides.yours.map((one) => handleStem(one.name)),
      SIDE_HEADINGS.yours,
    ),
    theirs: sideName(
      sides.theirs.map((one) => handleStem(one.name)),
      SIDE_HEADINGS.theirs,
    ),
  };

  return (
    <>
      {/* **The three figures, and no names over them.** The bar directly beneath labels both
          of its segments, so a name here would sit two lines above the same name — and the
          figures line up over the fold they describe. The spoken name still carries whose
          each strength is (`splitRowLabel`), because a listener has no band to read. */}
      <View style={s.split} accessible accessibilityLabel={splitRowLabel(spoken, split)}>
        <Text style={[s.sideLevel, s.sideYours]}>{formatLevel(split.yourSide)}</Text>

        {/* **Signed, as it was served.** Taking the sign off would be this card doing
            arithmetic over a number it was handed. */}
        <Text style={s.gap}>
          {GAP_WORD} {formatLevel(split.gap)}
        </Text>

        <Text style={[s.sideLevel, s.sideTheirs]}>{formatLevel(split.theirSide)}</Text>
      </View>

      {/* Drawn and hidden: the row above prints all three of the bar's numbers, so its own name
          would be the fourth reading of one fact (§20.1's merge rule). */}
      <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
        <BalanceBar
          advantage={split.gap}
          tone={tone}
          size="md"
          variant="onDark"
          labels={[drawn.yours, drawn.theirs]}
          accessibilityLabel={balanceLabel(forecast.pct)}
        />
      </View>
    </>
  );
}

/**
 * A seat as the read-only court needs it — **an id and a link, and nothing else.**
 *
 * Deliberately less than the builder's `toOccupant`: a face needs neither the name, the level
 * nor the acceptance, and your own seat carries no `photoUrl` because no route serves a
 * searcher their own card — so it draws the poster its id already produces.
 *
 * **Not read off `handlesOn`'s `face`, which carries the same two fields.** That function
 * returns the people on a half and drops the empty seats, and a court is drawn by **position**
 * — so building its children from handles would seat everybody one hole to the left.
 */
function faceOf(
  seat: Seating[number],
  court: { readonly rows: ReadonlyMap<string, Candidate>; readonly self: string | undefined },
): CourtFaceOccupant {
  if (seat.kind === 'you') {
    return { kind: 'you', ...(court.self === undefined ? {} : { playerId: court.self }) };
  }
  if (seat.kind === 'empty') return { kind: 'empty' };

  const photo = court.rows.get(seat.playerId)?.card.photoUrl;
  return {
    kind: 'player',
    playerId: seat.playerId,
    ...(photo === undefined ? {} : { photoUrl: photo }),
  };
}

const s = StyleSheet.create({
  card: { gap: theme.space.sm },
  top: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  /** `flex: 1` so the *Court* control keeps its width and the names take what is left. */
  claim: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  who: { flex: 1, gap: theme.space.xxs },
  /** The picture and its one word, as one column — the word centred on the court's width. */
  court: { alignItems: 'center', gap: theme.space.xxs },
  sport: {
    ...theme.type.eyebrow,
    color: theme.color.onDarkTiny,
    textAlign: 'center',
    textTransform: 'uppercase',
  },
  count: { ...theme.type.cardTitle, color: theme.color.surface },
  figure: { ...theme.num.l, ...theme.tabular, color: theme.color.surface },
  split: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  sideYours: { textAlign: 'left' },
  sideTheirs: { textAlign: 'right' },
  sideLevel: { ...theme.num.xs, ...theme.tabular, color: theme.color.surface, flex: 1 },
  gap: { ...theme.type.tiny, color: theme.color.onDarkTiny },
  body: { ...theme.type.tiny, color: theme.color.onDarkTiny },
});
