/**
 * The three card types, drawn.
 *
 * **This is the spine and the status line, and deliberately not the whole card.**
 * `ADR-0070` splits a card into the half every phone can draw and the half only a
 * current one can, and both are here; what is *not* here is the action row's three
 * slots, the countdown, the fit badge and the emphasis flag — those are the match
 * card's own ticket (`Raketa02/Raketa#87`) and the shelves' (`#88`), which grow
 * this file rather than replacing it. Nothing below decides where a tap goes,
 * because nothing below has a tap.
 *
 * **A situation this build has never heard of draws the spine and drops the status
 * line.** It is never skipped: an app hiding a match the player has paid for is
 * the worst outcome on `ADR-0070`'s list and reads as *your app lost my booking*.
 * Losing the sentence loses exactly the thing that is actually missing, and the
 * mapper has already expressed that as `status === undefined`.
 *
 * A person and a club card have no situation half at all — three card types, not
 * one with holes.
 */

import { StyleSheet, Text, View } from 'react-native';

import { formatMoney } from '@/shared/lib/formatting';
import { Card, Note, Tag, theme } from '@/shared/ui';

import type { ClubCard, MatchCard, NowCard, PersonCard } from '../domain/ComposedScreen';

import { TONE_PRESENTATION } from './tonePresentation';

/** The metadata separator, everywhere on this screen without exception. */
const SEP = ' · ';

export interface NowCardViewProps {
  readonly card: NowCard;
}

export function NowCardView({ card }: NowCardViewProps) {
  switch (card.kind) {
    case 'match':
      return <MatchCardView card={card} />;
    case 'person':
      return <PersonCardView card={card} />;
    case 'club':
      return <ClubCardView card={card} />;
  }
}

export interface MatchCardViewProps {
  readonly card: MatchCard;
}

export function MatchCardView({ card }: MatchCardViewProps) {
  const tone = card.status === undefined ? undefined : TONE_PRESENTATION[card.status.tone];

  return (
    <View style={s.stack}>
      {card.status?.alert != null ? (
        // The strip above the card, on the three situations that leave a player
        // short of a player inside the rescue window.
        <Note variant="coral" accessibilityRole="alert">
          {card.status.alert}
        </Note>
      ) : null}

      <Card style={s.card}>
        {card.status !== undefined && tone !== undefined ? (
          <Tag label={card.status.tag} variant={tone.variant} dot={tone.dot} />
        ) : null}

        {card.status !== undefined ? <Text style={s.line}>{card.status.line}</Text> : null}

        <Text style={s.meta}>
          {[card.where.clubName, card.where.cover, distance(card.where.distanceKm)]
            .filter((part): part is string => part !== undefined)
            .join(SEP)}
        </Text>

        <Text style={s.price}>{formatMoney(card.price)}</Text>
      </Card>
    </View>
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
  title: { ...theme.type.cardTitle, color: theme.color.ink },
  line: { ...theme.type.tiny, color: theme.color.ink },
  meta: { ...theme.type.tiny, color: theme.color.muted },
  price: { ...theme.num.s, ...theme.tabular, color: theme.color.ink },
});
