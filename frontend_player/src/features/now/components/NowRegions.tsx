/**
 * The three regions, top to bottom: offers, the enrolled strip, the shelves.
 *
 * **A region is present and empty, never absent** (`ADR-0070`). That is one code
 * path instead of two, and it is why a player with nothing still gets a shape she
 * recognises rather than a blank page. What differs between the three is what
 * *empty* looks like:
 *
 * - **Offers** draw nothing at all when there are none. The region exists; it makes
 *   no claim, and a permanent row saying *no seats have opened* is exactly the
 *   furniture `ADR-0050` refuses.
 * - **Your matches** draws its own empty card, because a player in nothing is a
 *   state the strip is about.
 * - **The shelves** draw the honest empty city — never invented players.
 *
 * **The order within a region is the server's** and is fixed at composition:
 * offers soonest-to-expire, the strip chronological, the shelves in the server's
 * own list. Nothing here sorts, filters or drops a card. `ADR-0032`: order is a
 * property of the composed screen.
 *
 * **Two of the three regions draw a state card and one draws a shelf card**
 * (`ADR-0088`). All three hand their cards the same handler; what differs is how a
 * card reaches it — the state card through a labelled button in its action row, the
 * shelf card through its whole body, and only when it names an act.
 *
 * **Every shelf ends in a card into Find, and the client appends it.** The tail card
 * is not in the contract: it is composed from the shelf's own code and the sport the
 * screen is already filtered to, which is the same composition the door's sentence
 * makes. A shelf running out is a door and not a wall.
 */

import { ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';

import { Card, PressableCard, theme } from '@/shared/ui';

import type {
  Block,
  EnrolledRegion,
  NowCard,
  OffersRegion,
  ShelvesRegion,
} from '../domain/ComposedScreen';
import type { SportFilter } from '../mappers/codes';
import { findPreFilter, type FindPreFilter } from '../mappers/shelves';

import type { CardControl } from './ActionRow';
import { MatchCardView, NowCardView } from './NowCards';
import { DoorView } from './NowDoor';
import {
  FIND_TAIL_LABEL,
  NO_MATCHES_BOOKED,
  REGION_HEADING,
  findTailLabel,
  nothingOpen,
} from './nowCopy';
import { GUTTER, STRIP_GAP, contentWidth, railCardWidth, stripSnapInterval } from './nowGeometry';

/** The region test ids, so *present and empty* is assertable rather than implied. */
export const REGION_ID = {
  offers: 'now-region-offers',
  yourMatches: 'now-region-your-matches',
  shelves: 'now-region-shelves',
} as const;

/** The card at the end of a shelf, so *every shelf has one* is assertable. */
export const TAIL_CARD_ID = 'now-shelf-tail';

export function SectionHeading({ title }: { readonly title: string }) {
  return (
    <Text style={s.heading} accessibilityRole="header">
      {title}
    </Text>
  );
}

/**
 * Seats offered to this viewer, above everything.
 *
 * The thing with a clock is first. Vertical rather than a strip: an offer is not
 * something to swipe past, and there is rarely more than one.
 */
export function OffersRegionView({
  region,
  onControl,
  busyMatchId,
}: {
  readonly region: OffersRegion;
  readonly onControl: (control: CardControl) => void;
  /**
   * The match whose seat is being taken right now, if one is.
   *
   * This region alone, because this region alone holds an act that is a **write**
   * rather than a route: taking a seat is answered by the card itself, so the
   * button has to say it is working. The strip's acts all open a screen, which is
   * its own answer — a card there gains this the day it holds a write of its own
   * (`Raketa02/Raketa#92`), and not before, because a prop nothing sets is a prop
   * nobody can be sure is read.
   */
  readonly busyMatchId?: string;
}) {
  return (
    <View testID={REGION_ID.offers} style={region.cards.length === 0 ? undefined : s.region}>
      {region.cards.length === 0 ? null : (
        <>
          <SectionHeading title={REGION_HEADING.offers} />
          <View style={s.column}>
            {region.cards.map((card) => (
              // A column, so no card is stretched and `fill` stays off: an auto top
              // margin with no free space above it is worth nothing here.
              <MatchCardView
                key={card.matchId}
                card={card}
                onControl={onControl}
                busy={card.matchId === busyMatchId}
              />
            ))}
          </View>
        </>
      )}
    </View>
  );
}

/**
 * The matches she is committed to, as `.hstrip` — one card at a time, bled to the
 * frame edge, with the next one peeking by `gutter − gap`.
 *
 * **Not `.mrail`.** `UI` §D5 says in as many words that the rail *"is not used by
 * Now"*, and `size.railCardRatio` is the rail's; applied here it shows a quarter of
 * the next card's *contents*, which reads as two cards rather than as a peek. The
 * child is the full content width at every screen width, so the peek is the same
 * 6pt on a 320pt phone and on a 430pt one.
 */
export function EnrolledStripView({
  region,
  onControl,
}: {
  readonly region: EnrolledRegion;
  readonly onControl: (control: CardControl) => void;
}) {
  const { width } = useWindowDimensions();
  const cardWidth = contentWidth(width);

  return (
    <View testID={REGION_ID.yourMatches} style={s.region}>
      <SectionHeading title={REGION_HEADING.yourMatches} />

      {region.cards.length === 0 ? (
        <View style={s.gutter}>
          <Card>
            <Text style={s.empty}>{NO_MATCHES_BOOKED}</Text>
          </Card>
        </View>
      ) : (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          // One flick moves one card, per `deltas/native-kit.md` §6.
          snapToInterval={stripSnapInterval(width)}
          disableIntervalMomentum
          decelerationRate="fast"
          style={s.strip}
          contentContainerStyle={s.stripContent}
        >
          {region.cards.map((card) => (
            <View key={card.matchId} style={{ width: cardWidth }}>
              {/* A row stretches its children to the tallest, so `fill` is what
                  gives the action row's `marginTop: auto` a height to push
                  against — `native-kit.md` §3's answer to the slab of empty
                  night under a short card. */}
              <MatchCardView card={card} onControl={onControl} fill />
            </View>
          ))}
        </ScrollView>
      )}
    </View>
  );
}

/**
 * The blocks, in the server's order. A shelf with nothing in it never arrives.
 *
 * Each shelf is a **rail** rather than a strip: its child is `size.railCardRatio`
 * of the column, so a quarter of the next card shows and the row says *there are
 * more*. That ratio is the rail's own and is correct here; what
 * `deltas/native-kit.md` forbids is applying it to the **strip** above, whose child
 * is the full content width.
 *
 * **The list is not homogeneous, and that is the contract** (`ADR-0084`). One entry
 * may be the door into a sport this viewer holds no rating at, and it is drawn
 * where it arrives — in the position the ranked shelves would occupy, with *New on
 * Raketa* and *New clubs* beneath it. Nothing here decides that: a door is drawn
 * exactly when the server sent one, and the emptiness of a list is never read as
 * one, because a genuinely empty city in a sport she **is** rated at looks
 * identical from here.
 */
export function ShelvesRegionView({
  region,
  sport,
  onEnterDoor,
  onControl,
  onOpenFind,
}: {
  readonly region: ShelvesRegion;
  readonly sport: SportFilter;
  readonly onEnterDoor: () => void;
  readonly onControl: (control: CardControl) => void;
  readonly onOpenFind: (preFilter: FindPreFilter) => void;
}) {
  const { width } = useWindowDimensions();

  return (
    <View testID={REGION_ID.shelves}>
      {region.blocks.length === 0 ? (
        <View style={[s.region, s.gutter]}>
          <Card>
            <Text style={s.empty}>{nothingOpen(sport)}</Text>
          </Card>
        </View>
      ) : (
        region.blocks.map((block) =>
          block.kind === 'door' ? (
            <DoorView key={blockKey(block)} door={block} onEnter={onEnterDoor} />
          ) : (
            <View key={blockKey(block)} style={s.region}>
              {block.title !== undefined ? <SectionHeading title={block.title} /> : null}
              {block.caption !== undefined ? (
                <Text style={[s.caption, s.gutter]}>{block.caption}</Text>
              ) : null}

              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={s.shelfContent}
              >
                {block.cards.map((card) => (
                  <View key={cardKey(card)} style={{ width: railCardWidth(width) }}>
                    <NowCardView card={card} onControl={onControl} fill />
                  </View>
                ))}

                <ShelfTailCard
                  code={block.code}
                  title={block.title}
                  sport={sport}
                  width={railCardWidth(width)}
                  onOpenFind={onOpenFind}
                />
              </ScrollView>
            </View>
          ),
        )
      )}
    </View>
  );
}

/**
 * The card every shelf ends in: a door into Find, never a wall.
 *
 * **It is not in the contract, and that is the decision** (`ADR-0070`, granted for
 * exactly this card): the client appends it, composing the shelf's own claim with
 * the sport it is already filtered to. A tail card on the wire would be a card the
 * server sends that is not about a match, a person or a club, and its destination is
 * a client-side route in any case.
 *
 * **A shelf whose code this build has never heard of gets none.** `findPreFilter`
 * answers `undefined` for it, which is the same answer as *do not draw the tail
 * card* — a door this build cannot address is worse than no door, and the shelf's
 * title is missing for the same reason at the same moment.
 */
function ShelfTailCard({
  code,
  title,
  sport,
  width,
  onOpenFind,
}: {
  readonly code: string;
  readonly title: string | undefined;
  readonly sport: SportFilter;
  readonly width: number;
  readonly onOpenFind: (preFilter: FindPreFilter) => void;
}) {
  const preFilter = findPreFilter(code, sport);
  if (preFilter === undefined) return null;

  return (
    // The id sits on the wrapper because a design-system primitive owns its own
    // test ids and takes none; the press is reached by the label it announces.
    <View testID={TAIL_CARD_ID} style={{ width }}>
      <PressableCard
        style={s.tail}
        onPress={() => onOpenFind(preFilter)}
        accessibilityLabel={findTailLabel(title)}
      >
        <Text style={s.tailLabel}>{FIND_TAIL_LABEL}</Text>
      </PressableCard>
    </View>
  );
}

/** A block is identified by what it is, so a door and a shelf cannot collide. */
function blockKey(block: Block): string {
  return `${block.kind}:${block.code}`;
}

/** A card is identified by the thing it is about, never by its position. */
function cardKey(card: NowCard): string {
  switch (card.kind) {
    case 'match':
      return card.matchId;
    case 'person':
      return card.playerId;
    case 'club':
      return card.clubId;
  }
}

const s = StyleSheet.create({
  region: { gap: theme.space.sm, marginBottom: theme.space.xl },
  gutter: { paddingHorizontal: GUTTER },
  column: { paddingHorizontal: GUTTER, gap: theme.space.sm },
  heading: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: 'uppercase',
    paddingHorizontal: GUTTER,
  },
  caption: { ...theme.type.tiny, color: theme.color.muted },
  // The tail is the shelf's own height, so the rail does not step down at its end.
  tail: { flex: 1, justifyContent: 'center' },
  tailLabel: { ...theme.type.inlineTitle, color: theme.color.ink },
  empty: { ...theme.type.tiny, color: theme.color.muted },
  // The negative margin is what lets the strip bleed to the screen edge while its
  // content still aligns to the gutter (`design-system.md` Part 8).
  strip: { marginHorizontal: -GUTTER },
  stripContent: { paddingHorizontal: GUTTER, gap: STRIP_GAP },
  shelfContent: { paddingHorizontal: GUTTER, gap: theme.space.sm },
});
