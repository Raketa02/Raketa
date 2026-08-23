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
 * The shelf-level rules — the tail card into Find, absence versus the empty card,
 * the fit badge, emphasis — are `Raketa02/Raketa#88`'s and land on top of this.
 */

import { ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';

import { Card, theme } from '@/shared/ui';

import type {
  EnrolledRegion,
  NowCard,
  OffersRegion,
  ShelvesRegion,
} from '../domain/ComposedScreen';
import type { SportFilter } from '../mappers/codes';

import { MatchCardView, NowCardView } from './NowCards';
import { NO_MATCHES_BOOKED, REGION_HEADING, nothingOpen } from './nowCopy';
import { GUTTER, STRIP_GAP, contentWidth, railCardWidth, stripSnapInterval } from './nowGeometry';

/** The region test ids, so *present and empty* is assertable rather than implied. */
export const REGION_ID = {
  offers: 'now-region-offers',
  yourMatches: 'now-region-your-matches',
  shelves: 'now-region-shelves',
} as const;

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
export function OffersRegionView({ region }: { readonly region: OffersRegion }) {
  return (
    <View testID={REGION_ID.offers} style={region.cards.length === 0 ? undefined : s.region}>
      {region.cards.length === 0 ? null : (
        <>
          <SectionHeading title={REGION_HEADING.offers} />
          <View style={s.column}>
            {region.cards.map((card) => (
              <MatchCardView key={card.matchId} card={card} />
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
export function EnrolledStripView({ region }: { readonly region: EnrolledRegion }) {
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
              <MatchCardView card={card} />
            </View>
          ))}
        </ScrollView>
      )}
    </View>
  );
}

/**
 * The shelves, in the server's order. A shelf with nothing in it never arrives.
 *
 * Each is a **rail** rather than a strip: its child is `size.railCardRatio` of the
 * column, so a quarter of the next card shows and the row says *there are more*.
 * That ratio is the rail's own and is correct here; what
 * `deltas/native-kit.md` forbids is applying it to the **strip** above, whose child
 * is the full content width.
 */
export function ShelvesRegionView({
  region,
  sport,
}: {
  readonly region: ShelvesRegion;
  readonly sport: SportFilter;
}) {
  const { width } = useWindowDimensions();

  return (
    <View testID={REGION_ID.shelves}>
      {region.shelves.length === 0 ? (
        <View style={[s.region, s.gutter]}>
          <Card>
            <Text style={s.empty}>{nothingOpen(sport)}</Text>
          </Card>
        </View>
      ) : (
        region.shelves.map((shelf) => (
          <View key={shelf.code} style={s.region}>
            {shelf.title !== undefined ? <SectionHeading title={shelf.title} /> : null}
            {shelf.caption !== undefined ? (
              <Text style={[s.caption, s.gutter]}>{shelf.caption}</Text>
            ) : null}

            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={s.shelfContent}
            >
              {shelf.cards.map((card) => (
                <View key={cardKey(card)} style={{ width: railCardWidth(width) }}>
                  <NowCardView card={card} />
                </View>
              ))}
            </ScrollView>
          </View>
        ))
      )}
    </View>
  );
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
  empty: { ...theme.type.tiny, color: theme.color.muted },
  // The negative margin is what lets the strip bleed to the screen edge while its
  // content still aligns to the gutter (`design-system.md` Part 8).
  strip: { marginHorizontal: -GUTTER },
  stripContent: { paddingHorizontal: GUTTER, gap: STRIP_GAP },
  shelfContent: { paddingHorizontal: GUTTER, gap: theme.space.sm },
});
