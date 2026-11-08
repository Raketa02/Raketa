/**
 * **A miniature game card** — one of the three sign-in's hero deals
 * ([#786](https://github.com/Raketa02/Raketa/issues/786), PRD #783; design system 12.2, mock 2).
 *
 * ```
 * ┌─────────────────────────────────┐
 * │ Seat open             ⏱ 21 h 00 │  the ribbon — coralInk on a seat open, the deck's teal, or green
 * ├─────────────────────────────────┤
 * │ [ karol.t     ] [ ania.k      ] │  the tiles — a poster, the nickname and its line on the scrim
 * │ [ kuba.w      ] ┊ You complete ┊ │  the reader's seat dashed volt; an empty seat dashed grey
 * │ 91%  [ karol.t + You │ ania.k… ] │  the forecast — the figure, and the bar, your side left
 * │ ┌ Sat 16:00 · Ogrody 33  27 zł ┐ │  the booking strip — the line, and the share in volt
 * └─────────────────────────────────┘
 * ```
 *
 * ## An illustration copied from the card, not the card
 *
 * The live Games card (`proposals`' `GameCard`) is not made public and not changed for this: auth
 * importing it would be an auth ↔ proposals cycle, since the app's gate already reaches auth, and it
 * would bend a live component around a sign-in picture. So this is the card's **look**, redrawn
 * from what shared UI already makes public — the poster, the balance bar and the theme — with the
 * real card's own roles, colours and corners, and plain props in place of a proposal. **The cost is
 * written down** (`docs/features/auth.md`): a later redesign of the game card does not reach this by
 * itself, so whoever changes the card checks the hero.
 *
 * Where mock 2 draws the card differently from the app, **the mock wins**, because this is a
 * picture of the mock: no *vs* line and no week grid; a booking strip of one line, its border the
 * booked court's volt stroke on every card; the reader's seat with its words alone; and a green
 * ribbon for a Fill in. **One departure the other way**: the tile rows are equal, as the live card
 * draws them, where the mock draws the top row about half the bottom's — a row that short would be
 * its scrim and nothing else.
 *
 * ## Drawn at one size, and scaled with the deck
 *
 * At `size.stage.card` — twice mock 2's miniature, where the mock's words measure the real card's
 * own roles — and never laid out against the screen: the deck scales the three together to the
 * hero's room (`stageDeckGeometry`). Its words are capped at the hero's `textMaxScale`, as the
 * headline is, and each sits on one line, so a large text setting cuts a name rather than pushing
 * the card's parts out of its box.
 *
 * It says nothing to a screen reader: the hero around it is hidden whole (ADR-0198).
 */

import Feather from '@expo/vector-icons/Feather';
import { useId } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import Svg, { Defs, LinearGradient, Rect, Stop } from 'react-native-svg';

import {
  BalanceBar,
  CourtPoster,
  POSTER_LABEL,
  theme,
  type BalanceBarTone,
  type CourtPosterLook,
} from '@/shared/ui';

/** One seat on a miniature card. */
export type MiniSeat =
  /** Somebody on the game: their poster, their nickname, and their Level (and *paid*). */
  | {
      readonly kind: 'person';
      readonly name: string;
      readonly line: string;
      readonly look: CourtPosterLook;
    }
  /** The reader's own seat, offered: dashed volt, its words alone. */
  | { readonly kind: 'yours'; readonly words: string }
  /** A seat nobody is in: dashed grey, nothing in it. */
  | { readonly kind: 'empty' };

/** Which ribbon's bed: a seat open (coralInk), a game dealt (the deck's teal), a Fill in (green). */
export type MiniRibbonTone = 'seatOpen' | 'dealt' | 'fillIn';

export interface MiniGameCardProps {
  readonly ribbon: {
    readonly words: string;
    readonly tone: MiniRibbonTone;
    /** The countdown, drawn — *21 h 00*. Absent with a day or more to go, as on the real card. */
    readonly clock?: string;
  };
  /** The tiles, the top row first — two rows in doubles, one of two tall tiles in singles. */
  readonly rows: readonly (readonly MiniSeat[])[];
  readonly forecast: {
    /** *91%*, drawn. */
    readonly figure: string;
    readonly tone: BalanceBarTone;
    /** Yours, then theirs. */
    readonly labels: readonly [string, string];
  };
  readonly booking: {
    /** *Sat 16:00 · Ogrody 33*. */
    readonly when: string;
    /** *27 zł*, drawn. */
    readonly share: string;
  };
}

const CAP = theme.size.stage.textMaxScale;

/** The forecast's figure on the card's ground — the real card's three (`FORECAST_FIGURE`). */
const FORECAST_FIGURE: Readonly<Record<BalanceBarTone, string>> = {
  ok: theme.color.gameGreen,
  warn: theme.color.gameAmber,
  bad: theme.color.gameRed,
};

export function MiniGameCard({ ribbon, rows, forecast, booking }: MiniGameCardProps) {
  return (
    <View style={s.card}>
      <View style={s.clip}>
        <MiniGround />

        <View style={[s.ribbon, RIBBON[ribbon.tone]]}>
          <Text style={s.ribbonWords} numberOfLines={1} maxFontSizeMultiplier={CAP}>
            {ribbon.words}
          </Text>
          {ribbon.clock === undefined ? null : (
            <View style={s.clock}>
              <Feather name="clock" size={theme.size.infoGlyph} color={theme.color.surface} />
              <Text style={s.clockWords} numberOfLines={1} maxFontSizeMultiplier={CAP}>
                {ribbon.clock}
              </Text>
            </View>
          )}
        </View>

        <View style={s.body}>
          <View style={s.tiles}>
            {rows.map((row, at) => (
              <View key={at} style={s.row}>
                {row.map((seat, place) => (
                  <MiniTile key={place} seat={seat} />
                ))}
              </View>
            ))}
          </View>

          <View style={s.forecast}>
            <Text
              style={[s.figure, { color: FORECAST_FIGURE[forecast.tone] }]}
              numberOfLines={1}
              maxFontSizeMultiplier={CAP}
            >
              {forecast.figure}
            </Text>
            <View style={s.bar}>
              {/* The fold at the centre, where mock 2 draws it: nobody's Level is the reader's. */}
              <BalanceBar
                advantage={0}
                tone={forecast.tone}
                size="lg"
                variant="onDark"
                labels={forecast.labels}
                accessibilityLabel={forecast.figure}
              />
            </View>
          </View>

          <View style={s.booking}>
            <Text style={s.when} numberOfLines={1} maxFontSizeMultiplier={CAP}>
              {booking.when}
            </Text>
            <Text style={s.share} numberOfLines={1} maxFontSizeMultiplier={CAP}>
              {booking.share}
            </Text>
          </View>
        </View>
      </View>
    </View>
  );
}

function MiniTile({ seat }: { readonly seat: MiniSeat }) {
  switch (seat.kind) {
    case 'empty':
      return <View style={[s.tile, s.dashed, s.empty]} testID="stage-seat-empty" />;
    case 'yours':
      return (
        <View style={[s.tile, s.dashed, s.yours]}>
          <Text style={s.yoursWords} numberOfLines={2} maxFontSizeMultiplier={CAP}>
            {seat.words}
          </Text>
        </View>
      );
    case 'person':
      return (
        <View style={s.tile}>
          <CourtPoster
            hue={seat.look.hue}
            pose={seat.look.pose}
            accessibilityLabel={POSTER_LABEL}
            style={StyleSheet.absoluteFill}
          />
          {/* The real tile's pinned scrim under the words: white over the brightest poster there
              can be is 5,24 (`photoScrim`). */}
          <View style={s.foot}>
            <Text style={s.name} numberOfLines={1} maxFontSizeMultiplier={CAP}>
              {seat.name}
            </Text>
            <Text style={s.line} numberOfLines={1} maxFontSizeMultiplier={CAP}>
              {seat.line}
            </Text>
          </View>
        </View>
      );
  }
}

/**
 * The real card's ground, redrawn: one gradient down the card from `gameGroundTop` to
 * `gameGroundFoot` (Part 16 2026-09-30) — `GameGround`'s drawing, which is the card's and not public.
 * The id is per instance, because three cards are in the hero at once.
 */
function MiniGround() {
  const ground = `${useId()}-ground`;
  return (
    <View style={StyleSheet.absoluteFill} pointerEvents="none">
      <Svg width="100%" height="100%" viewBox="0 0 1 1" preserveAspectRatio="none">
        <Defs>
          <LinearGradient id={ground} x1="0" y1="0" x2="0" y2="1">
            <Stop offset={0} stopColor={theme.color.gameGroundTop} />
            <Stop offset={1} stopColor={theme.color.gameGroundFoot} />
          </LinearGradient>
        </Defs>
        <Rect x={0} y={0} width={1} height={1} fill={`url(#${ground})`} />
      </Svg>
    </View>
  );
}

const CARD = theme.size.stage.card;

const s = StyleSheet.create({
  // The real card's corner and its floating shadow (4.3's deck card).
  card: {
    width: CARD.width,
    height: CARD.height,
    borderRadius: theme.radius.deckCard,
    ...theme.shadow.deckCard,
  },
  clip: { flex: 1, borderRadius: theme.radius.deckCard, overflow: 'hidden' },
  ribbon: {
    height: CARD.ribbon,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: theme.space.lg,
    gap: theme.space.sm,
  },
  ribbonWords: { ...theme.type.h2, color: theme.color.surface, flexShrink: 1 },
  clock: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xxs },
  clockWords: { ...theme.num.xs, ...theme.tabular, color: theme.color.surface },
  body: { flex: 1, padding: theme.space.md, gap: theme.space.sm },
  tiles: { flex: 1, gap: theme.space.sm },
  row: { flex: 1, flexDirection: 'row', gap: theme.space.sm },
  tile: {
    flex: 1,
    borderRadius: theme.radius.card,
    overflow: 'hidden',
    justifyContent: 'flex-end',
  },
  // A seat nobody is in yet, the real card's way: dashed at the court block's stroke.
  dashed: { borderWidth: theme.size.gameCard.courtStroke, borderStyle: 'dashed' },
  // The real empty seat, in the on-dark hair.
  empty: { borderColor: theme.color.onDarkHair },
  // The real open seat: volt as a line, which it may be on dark (2.2).
  yours: {
    borderColor: theme.color.volt,
    justifyContent: 'center',
    alignItems: 'center',
    padding: theme.space.sm,
  },
  yoursWords: { ...theme.type.h2, color: theme.color.volt, textAlign: 'center' },
  foot: {
    backgroundColor: theme.color.photoScrim,
    paddingHorizontal: theme.space.sm,
    paddingVertical: theme.space.xs,
    gap: theme.space.xxs,
  },
  name: { ...theme.type.h2, color: theme.color.surface },
  line: { ...theme.num.xs, ...theme.tabular, color: theme.color.onDarkTiny },
  forecast: { flexDirection: 'row', alignItems: 'center', gap: theme.space.md },
  figure: { ...theme.num.xl, ...theme.tabular },
  bar: { flex: 1 },
  // One line, where the real court block has a tag over it — mock 2's strip — on the booked bed
  // with volt's own stroke (`CourtBlock`'s *Booked*).
  booking: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: theme.space.sm,
    borderRadius: theme.radius.card,
    borderWidth: theme.size.gameCard.courtStroke,
    borderColor: theme.color.voltStroke,
    backgroundColor: theme.color.gameCourtBooked,
    padding: theme.space.md,
  },
  when: { ...theme.type.h2, color: theme.color.surface, flexShrink: 1 },
  share: { ...theme.num.m, ...theme.tabular, color: theme.color.volt },
});

/** Each ribbon's bed — the real card's two, and mock 2's green for a Fill in. */
const RIBBON = StyleSheet.create({
  // White on coralInk is 5,89 — the real rescue ribbon's.
  seatOpen: { backgroundColor: theme.color.coralInk },
  dealt: { backgroundColor: theme.color.gameRibbon },
  // Mock 2's green, which is the card's own forecast green; white on it is 4,62.
  fillIn: { backgroundColor: theme.color.gameGreen },
});
