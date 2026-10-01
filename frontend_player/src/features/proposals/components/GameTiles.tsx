/**
 * **The people on a game card** — two rows of tiles, one side each, and the *vs* line between them
 * (the screens A2.3; mocks 2–8, 10; details 8).
 *
 * ```
 * ┌ photo / poster ──────┐ ┌──────────────────────┐
 * │                      │ │                      │
 * │ Karol Tomaszewski IN │ │ You                  │   the name, whole — cut by the box — and IN
 * │ 2,75                 │ │ You complete it      │   the Level, or what your yes would do
 * └──────────────────────┘ └──────────────────────┘
 * ───── KAROL + ZOFIA  VS  ANIA + YOU ─────             stems, uppercased by the style
 * ```
 *
 * **Which row is on top is the domain's** (`rowsOf`): the side with more people In, and on a tie
 * yours. Singles is one row of two tall tiles with no *vs* line (mock 10), because a line naming
 * one person against another says what the two tiles already do.
 *
 * ## A tile is the door to its player's record
 *
 * Every tile but yours opens `PlayerRecordSheet` (the screens A2.2) — a press, where the Players
 * deck asks for a long one, because on this card the tap has somewhere to go and the rest of the
 * card is the door to the game. Your own tile is part of that rest: it opens nothing of its own.
 * An empty seat is a dashed tile with nothing in it — a side short of a player, which the read
 * draws empty rather than inventing somebody.
 *
 * ## The name is whole, and the box cuts it
 *
 * ADR-0171: a tile shows the Name the player gave, and a narrow tile truncates it — one line,
 * tail cut — rather than drawing *Karol T.*, which is the mocks' own data and not a rule. Only the
 * *vs* line stems a name, because it holds four in one line.
 *
 * ## A rescue's open seat is yours, dashed
 *
 * On a *Seat open* card and on a rescue seen from outside (#557; mock 2), everybody else is *paid*
 * and the reader stands in the seat that opened: a **dashed volt** tile with no photograph, *You
 * complete it* over *27 zł · court booked* when it is the last seat, *You?* over *27 zł* while more
 * are open (the screens A2.3). The seat is offered, not taken — so no face.
 *
 * ## A booked game's tiles say *paid*
 *
 * The same tiles draw a booked game's people (#556; details 8): nobody on a booked court is *In* —
 * that word is a game still filling's — and each tile carries *paid* after its Level instead, the
 * share the club took.
 *
 * ## Two heights
 *
 * On the deck the tiles take the height the card leaves them (`fill`), down to `tileMin` on a short
 * phone, so the forecast, the grid and the court block keep theirs; on a game's details, where
 * nothing competes, each tile is drawn at the mock's width to height.
 */

import { Pressable, StyleSheet, Text, View } from 'react-native';

import { formatLevel } from '@/shared/formatting/ratingFormat';
import { PlayerPhoto, theme } from '@/shared/ui';

import type { DeckPerson, DeckRow, DeckSeat } from '../domain/deck';

import { CardTag } from './CardTag';
import {
  EMPTY_SEAT,
  LINE_JOIN,
  TILE_HINT,
  openSeatLabel,
  openSeatUnder,
  tileLabel,
  tileName,
  vsLine,
} from './deckPresentation';
import { PROPOSALS_COPY } from './proposalsCopy';

const COPY = PROPOSALS_COPY;

export interface GameTilesProps {
  readonly top: DeckRow;
  readonly bottom: DeckRow;
  /** One a side: one row of two tall tiles, and no *vs* line. */
  readonly singles: boolean;
  /** Your yes would leave no seat open — your tile says so, in volt. */
  readonly completes: boolean;
  /** Opens a player's record. Absent on a card behind the top one, which is a drawing only. */
  readonly onPerson?: (person: DeckPerson) => void;
  /** Take the card's spare height (the deck), or stand at the mock's proportion (the details). */
  readonly fill: boolean;
  /** A rescue: your tile is the open seat, offered at this share (*27 zł*). */
  readonly rescue?: { readonly share: string };
}

export function GameTiles({
  top,
  bottom,
  singles,
  completes,
  onPerson,
  fill,
  rescue,
}: GameTilesProps) {
  const tile = (seat: DeckSeat, at: number) =>
    rescue !== undefined && seat.kind === 'person' && seat.person.isYou ? (
      <OpenSeat key={seat.person.playerId} share={rescue.share} completes={completes} fill={fill} />
    ) : (
      <GameTile
        key={seat.kind === 'person' ? seat.person.playerId : `empty-${at}`}
        seat={seat}
        completes={completes}
        fill={fill}
        {...(onPerson === undefined ? {} : { onPerson })}
      />
    );

  if (singles) {
    return (
      <View style={[s.row, fill ? s.fill : undefined]}>
        {[...top.seats, ...bottom.seats].map(tile)}
      </View>
    );
  }

  return (
    <View style={[s.tiles, fill ? s.fill : undefined]}>
      <View style={[s.row, fill ? s.fill : undefined]}>{top.seats.map(tile)}</View>
      {/* The sides as a line, between the rows. Decorative to a listener: every tile names its
          person, and the card's sides are said once in the forecast's name. */}
      <View
        style={s.vs}
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
      >
        <View style={s.rule} />
        <Text style={s.vsWords} numberOfLines={1}>
          {vsLine(top, bottom)}
        </Text>
        <View style={s.rule} />
      </View>
      <View style={[s.row, fill ? s.fill : undefined]}>{bottom.seats.map(tile)}</View>
    </View>
  );
}

function GameTile({
  seat,
  completes,
  fill,
  onPerson,
}: {
  readonly seat: DeckSeat;
  readonly completes: boolean;
  readonly fill: boolean;
  readonly onPerson?: (person: DeckPerson) => void;
}) {
  const box = [s.tile, fill ? s.tileFill : s.tileFixed];

  if (seat.kind === 'empty') {
    return (
      <View
        style={[...box, s.empty]}
        accessible
        accessibilityLabel={EMPTY_SEAT}
        testID="game-tile-empty"
      />
    );
  }

  const { person } = seat;
  const drawing = (
    <>
      <View style={StyleSheet.absoluteFill}>
        <PlayerPhoto
          playerId={person.playerId}
          {...(person.photoUrl === undefined ? {} : { photoUrl: person.photoUrl })}
          box={{ kind: 'media' }}
        />
      </View>
      {/* The pinned scrim under the words: white over the brightest photograph there can be is
          5,24 (`photoScrim`), whatever the photograph is. */}
      <View style={s.foot}>
        <View style={s.nameRow}>
          <Text style={s.name} numberOfLines={1}>
            {tileName(person)}
          </Text>
          {person.isIn ? <CardTag label={COPY.in} tone="green" /> : null}
        </View>
        {person.isYou && completes ? (
          <Text style={s.completes} numberOfLines={1}>
            {COPY.youCompleteIt}
          </Text>
        ) : (
          <TileLine person={person} />
        )}
      </View>
    </>
  );

  if (person.isYou || onPerson === undefined) {
    return (
      <View
        style={box}
        accessible
        accessibilityLabel={tileLabel(person, completes)}
        testID={`game-tile-${person.playerId}`}
      >
        {drawing}
      </View>
    );
  }

  return (
    <Pressable
      style={({ pressed }) => [...box, pressed ? s.pressed : undefined]}
      accessibilityRole="button"
      accessibilityLabel={tileLabel(person, completes)}
      accessibilityHint={TILE_HINT}
      onPress={() => onPerson(person)}
      testID={`game-tile-${person.playerId}`}
    >
      {drawing}
    </Pressable>
  );
}

/**
 * **The seat a rescue offers you** (mock 2) — dashed volt, no face: *You complete it* over *27 zł ·
 * court booked*, or *You?* over *27 zł* while another seat is open too.
 */
function OpenSeat({
  share,
  completes,
  fill,
}: {
  readonly share: string;
  readonly completes: boolean;
  readonly fill: boolean;
}) {
  const under = openSeatUnder(share, completes);
  return (
    <View
      style={[s.tile, fill ? s.tileFill : s.tileFixed, s.openSeat]}
      accessible
      accessibilityLabel={openSeatLabel(completes, share)}
      testID="game-tile-your-seat"
    >
      <Text style={s.openSeatWho} numberOfLines={1}>
        {completes ? COPY.youCompleteIt : COPY.youQuestion}
      </Text>
      <Text style={s.openSeatShare} numberOfLines={1}>
        {under}
      </Text>
    </View>
  );
}

/**
 * Under the name: the Level, and on a booked game *paid* beside it — *2,71 · paid*, in the Level's
 * own mono (details 8). Nothing for an unrated player on a card still dealt.
 */
function TileLine({ person }: { readonly person: DeckPerson }) {
  const parts = [
    ...(person.level === undefined ? [] : [formatLevel(person.level)]),
    ...(person.paid === true ? [COPY.paid] : []),
  ];
  if (parts.length === 0) return null;
  return <Text style={s.level}>{parts.join(LINE_JOIN)}</Text>;
}

const s = StyleSheet.create({
  fill: { flex: 1 },
  tiles: { gap: theme.space.xs },
  row: { flexDirection: 'row', gap: theme.space.sm },
  tile: {
    flex: 1,
    borderRadius: theme.radius.card,
    overflow: 'hidden',
    justifyContent: 'flex-end',
  },
  tileFill: { minHeight: theme.size.gameCard.tileMin },
  tileFixed: { aspectRatio: theme.size.gameCard.detailsTile },
  empty: {
    borderWidth: theme.size.gameCard.courtStroke,
    borderStyle: 'dashed',
    borderColor: theme.color.onDarkHair,
  },
  // Volt as a line, which it may be on dark (2.2) — the seat offered, dashed because it is open.
  openSeat: {
    borderWidth: theme.size.gameCard.courtStroke,
    borderStyle: 'dashed',
    borderColor: theme.color.volt,
    justifyContent: 'center',
    alignItems: 'center',
    gap: theme.space.xxs,
    padding: theme.space.sm,
  },
  openSeatWho: { ...theme.type.h2, color: theme.color.volt },
  openSeatShare: { ...theme.num.xs, ...theme.tabular, color: theme.color.onDarkTiny },
  foot: {
    backgroundColor: theme.color.photoScrim,
    paddingHorizontal: theme.space.sm,
    paddingVertical: theme.space.xs,
    gap: theme.space.xxs,
  },
  nameRow: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  name: { ...theme.type.h2, color: theme.color.surface, flexShrink: 1 },
  level: { ...theme.num.xs, ...theme.tabular, color: theme.color.onDarkTiny },
  completes: { ...theme.num.xs, color: theme.color.volt },
  // 6.6's photo-tile value.
  pressed: { opacity: 0.7 },
  vs: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  rule: { flex: 1, height: StyleSheet.hairlineWidth, backgroundColor: theme.color.onDarkHair },
  vsWords: {
    ...theme.type.eyebrow,
    color: theme.color.onDarkEyebrow,
    textTransform: 'uppercase',
    flexShrink: 1,
  },
});
