/**
 * **The people on a game card** — two rows of tiles, one side each, and the *vs* line between them
 * (the screens A2.3; mocks 2–8, 10; details 8).
 *
 * ```
 * ┌ photo / poster ──────┐ ┌──────────────────────┐
 * │                      │ │                      │
 * │ karol.t IN           │ │ You                  │   the nickname, whole — cut by the box — and IN
 * │ 2,75                 │ │ You complete it      │   the Level, or what your yes would do
 * └──────────────────────┘ └──────────────────────┘
 * ───── KAROL + ZOFIA  VS  ANIA + YOU ─────             stems at the first dot, uppercased by the style
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
 * ## The nickname is whole, and the box cuts it
 *
 * ADR-0199 §1: a tile shows the nickname the player chose, without an @, and a narrow tile
 * truncates it — one line, tail cut — rather than drawing *Karol T.*, which is the mocks' own data
 * and not a rule. Only the *vs* line stems a nickname, because it holds four in one line.
 *
 * ## A rescue's open seat is yours, dashed
 *
 * On a *Seat open* card and on a rescue seen from outside (#557; mock 2), everybody else is *paid*
 * and the reader stands in the seat that opened: a **dashed volt** tile with no photograph, *You
 * complete it* over *27 zł · court booked* when it is the last seat, *You?* over *27 zł* while more
 * are open (the screens A2.3). The seat is offered, not taken — so no face.
 *
 * ## The reader's own friends carry FRIEND
 *
 * A **FRIEND** tag in volt after the name and its IN (#753; Q68, applying since Q128): only on the
 * reader's own friends, since the wire says nothing about who else is friends with whom. Volt is
 * the card's other tag fill (`CardTag`), so the two tags read as one family, and the name is what
 * the box cuts when both are there.
 *
 * ## A booked game's tiles say *paid*
 *
 * The same tiles draw a booked game's people (#556; details 8): nobody on a booked court is *In* —
 * that word is a game still filling's — and each tile carries *paid* after its Level instead, the
 * share the club took.
 *
 * ## One shape per court, and it never stretches
 *
 * A tile used to take whatever height the deck's card left it, so it was 1.90 : 1 on one phone and
 * 1.49 on another, and the wider it was the less face showed (#864). **It has one shape now** —
 * 1.75 : 1 on doubles and 3:4 on singles, the photo's own crop (`doublesTile`, `singlesTile`, with
 * their evidence) — and **the deck's card decides its size** (`deckCardGeometry`): as wide as its
 * column, or where the card's height runs out as tall as the room allows at the same shape,
 * narrower and centred, and the height left over goes to the card's gaps, never to a tile. The card
 * hands the size in (`geometry`) once it is laid out; until then a tile is its column's width at
 * its shape (`ratio`). **A game's details keep 1.75 for both court shapes** — no geometry, the
 * default ratio — so a singles tile is 3:4 on the deck and 1.75 there (#859, out of its scope).
 */

import { memo } from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  View,
  type LayoutChangeEvent,
  type ViewStyle,
} from 'react-native';

import { formatLevel } from '@/shared/formatting/ratingFormat';
import { PlayerPhoto, theme, type PlayerPhotoBox } from '@/shared/ui';

import type { DeckPerson, DeckRow, DeckSeat } from '../domain/deck';

import { CardTag } from './CardTag';
import type { TileGeometry } from './deckCardGeometry';
import {
  EMPTY_SEAT,
  LINE_JOIN,
  TILE_HINT,
  openSeatLabel,
  openSeatUnder,
  sidesSpoken,
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
  /**
   * **The deck's card**: each tile's size and the gaps inside the block, once the card is laid out
   * (`deckCardGeometry`). Absent, a tile is as wide as its column at `ratio`.
   */
  readonly geometry?: TileGeometry;
  /** A tile's width over its height where no `geometry` sizes it — `doublesTile`, the details'. */
  readonly ratio?: number;
  /** The *vs* line was laid out — the deck's card measures it (`deckCardGeometry`). */
  readonly onVsLaidOut?: (event: LayoutChangeEvent) => void;
  /** A rescue: your tile is the open seat, offered at this share (*27 zł*). */
  readonly rescue?: { readonly share: string };
  /**
   * **The card says its sides nowhere else** — no forecast is drawn, whose name says them: a
   * For-fun card's Social vibe (#838), or a card the server could not forecast. The *vs* line is
   * then spoken (`sidesSpoken`), so a listener still hears who partners whom. Absent, it is a
   * drawing.
   */
  readonly speaksSides?: boolean;
}

export function GameTiles({
  top,
  bottom,
  singles,
  completes,
  onPerson,
  geometry,
  ratio = theme.size.gameCard.doublesTile,
  onVsLaidOut,
  rescue,
  speaksSides = false,
}: GameTilesProps) {
  // Sized by the card, or its column's width at its shape — see the module note.
  const box: ViewStyle =
    geometry === undefined
      ? { flex: 1, aspectRatio: ratio }
      : { width: geometry.width, height: geometry.height, marginHorizontal: geometry.inset };

  const tile = (seat: DeckSeat, at: number) =>
    rescue !== undefined && seat.kind === 'person' && seat.person.isYou ? (
      <OpenSeat key={seat.person.playerId} share={rescue.share} completes={completes} box={box} />
    ) : (
      <GameTile
        key={seat.kind === 'person' ? seat.person.playerId : `empty-${at}`}
        seat={seat}
        completes={completes}
        box={box}
        {...(onPerson === undefined ? {} : { onPerson })}
      />
    );

  const row = [s.row, geometry === undefined ? undefined : { gap: geometry.across }];

  if (singles) {
    return <View style={row}>{[...top.seats, ...bottom.seats].map(tile)}</View>;
  }

  return (
    <View style={[s.tiles, geometry === undefined ? undefined : { gap: geometry.aroundVs }]}>
      <View style={row}>{top.seats.map(tile)}</View>
      {/* The sides as a line, between the rows. Decorative to a listener where the forecast's
          name says the sides; spoken where nothing else does (`speaksSides`) — said once. */}
      <View
        style={s.vs}
        testID="game-vs"
        {...(onVsLaidOut === undefined ? {} : { onLayout: onVsLaidOut })}
        {...(speaksSides
          ? { accessible: true, accessibilityLabel: sidesSpoken(top, bottom) }
          : {
              accessibilityElementsHidden: true,
              importantForAccessibility: 'no-hide-descendants',
            })}
      >
        <View style={s.rule} />
        <Text style={s.vsWords} numberOfLines={1}>
          {vsLine(top, bottom)}
        </Text>
        <View style={s.rule} />
      </View>
      <View style={row}>{bottom.seats.map(tile)}</View>
    </View>
  );
}

function GameTile({
  seat,
  completes,
  box: size,
  onPerson,
}: {
  readonly seat: DeckSeat;
  readonly completes: boolean;
  /** The tile's size — `GameTiles`' to decide. */
  readonly box: ViewStyle;
  readonly onPerson?: (person: DeckPerson) => void;
}) {
  const box = [s.tile, size];

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
      <TilePhoto playerId={person.playerId} photoUrl={person.photoUrl} />
      {/* The pinned scrim under the words: white over the brightest photograph there can be is
          5,24 (`photoScrim`), whatever the photograph is. */}
      <View style={s.foot}>
        <View style={s.nameRow}>
          <Text style={s.name} numberOfLines={1}>
            {tileName(person)}
          </Text>
          {person.isIn ? <CardTag label={COPY.in} tone="green" /> : null}
          {person.friend === true ? <CardTag label={COPY.friend} tone="volt" /> : null}
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

const MEDIA: PlayerPhotoBox = { kind: 'media' };

/**
 * **The photograph, or the poster**, edge to edge — drawn again only for another person or another
 * link. The deck's card resizes its tiles once it has measured itself (`deckCardGeometry`), and that
 * redraws the box, never the face in it.
 */
const TilePhoto = memo(function TilePhoto({
  playerId,
  photoUrl,
}: {
  readonly playerId: string;
  readonly photoUrl: string | undefined;
}) {
  return (
    <View style={StyleSheet.absoluteFill}>
      <PlayerPhoto
        playerId={playerId}
        {...(photoUrl === undefined ? {} : { photoUrl })}
        box={MEDIA}
      />
    </View>
  );
});

/**
 * **The seat a rescue offers you** (mock 2) — dashed volt, no face: *You complete it* over *27 zł ·
 * court booked*, or *You?* over *27 zł* while another seat is open too.
 */
function OpenSeat({
  share,
  completes,
  box,
}: {
  readonly share: string;
  readonly completes: boolean;
  readonly box: ViewStyle;
}) {
  const under = openSeatUnder(share, completes);
  return (
    <View
      style={[s.tile, box, s.openSeat]}
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
  // At rest: `deckCardGeometry`'s `aroundVs` and `across` before any spare height reaches them.
  tiles: { gap: theme.space.xs },
  row: { flexDirection: 'row', gap: theme.space.sm },
  tile: {
    borderRadius: theme.radius.card,
    overflow: 'hidden',
    justifyContent: 'flex-end',
  },
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
