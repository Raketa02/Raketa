/**
 * The three card types, drawn.
 *
 * A match card is the **spine**, the **status line** and — on a state card — the
 * **action row**. What is still not here is the fit badge and the emphasis flag:
 * those are the shelves' own ticket (`Raketa02/Raketa#88`), which grows this file
 * rather than replacing it.
 *
 * **A situation this build has never heard of draws the spine and drops the status
 * line.** It is never skipped: an app hiding a match the player has paid for is
 * the worst outcome on `ADR-0070`'s list and reads as *your app lost my booking*.
 * Losing the sentence loses exactly the thing that is actually missing, and the
 * mapper has already expressed that as `status === undefined`. The **action row is
 * unaffected**, because the act and `mayDepart` are spine facts: an unknown name
 * costs a phone one sentence and never the ability to take the seat.
 *
 * **Two card shapes, and `ADR-0088` says they are two.** The state card — the
 * strip and the offers region — reaches its act through a labelled button in the
 * action row, and takes the handler that answers it. The **shelf** card reaches
 * the same act through its whole body and gains no button, which is `#88`'s to
 * build; until then it draws no control at all rather than the wrong one, and it
 * cannot be handed one, because it takes no handler. That inconsistency is the
 * sharpest thing in `ADR-0088` and is accepted there rather than papered over: the
 * two were never the same component and never looked alike.
 *
 * A person and a club card have no situation half at all — three card types, not
 * one with holes.
 */

import { StyleSheet, Text, View } from 'react-native';
import type { ReactNode } from 'react';

import { formatMoney } from '@/shared/lib/formatting';
import { Card, Note, Tag, theme } from '@/shared/ui';

import type { ClubCard, MatchCard, NowCard, PersonCard } from '../domain/ComposedScreen';

import { ActionRow, type CardControl } from './ActionRow';
import { TONE_PRESENTATION } from './tonePresentation';

/** The metadata separator, everywhere on this screen without exception. */
const SEP = ' · ';

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
}

/** A shelf's card. It names no control, and takes no handler that could give it one. */
export function NowCardView({ card, fill = false }: NowCardViewProps) {
  switch (card.kind) {
    case 'match':
      return <ShelfMatchCardView card={card} fill={fill} />;
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
    <MatchCardShell card={card} fill={fill}>
      <ActionRow card={card} onControl={onControl} />
    </MatchCardShell>
  );
}

function ShelfMatchCardView({ card, fill }: { readonly card: MatchCard; readonly fill: boolean }) {
  return <MatchCardShell card={card} fill={fill} />;
}

/**
 * The half both shapes share: the alert strip, the status line and the spine.
 *
 * One body and two callers rather than one component with a shape flag — the flag
 * would be the sixth variant `ADR-0088` spent itself removing, one level up.
 */
function MatchCardShell({
  card,
  fill,
  children,
}: {
  readonly card: MatchCard;
  readonly fill: boolean;
  readonly children?: ReactNode;
}) {
  const tone = card.status === undefined ? undefined : TONE_PRESENTATION[card.status.tone];

  return (
    <View style={[s.stack, fill ? s.fill : undefined]}>
      {card.status?.alert != null ? (
        // The strip above the card, on the three situations that leave a player
        // short of a player inside the rescue window.
        <Note variant="coral" accessibilityRole="alert">
          {card.status.alert}
        </Note>
      ) : null}

      <Card style={[s.card, fill ? s.fill : undefined]}>
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

        {children}
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
  fill: { flex: 1 },
  title: { ...theme.type.cardTitle, color: theme.color.ink },
  line: { ...theme.type.tiny, color: theme.color.ink },
  meta: { ...theme.type.tiny, color: theme.color.muted },
  price: { ...theme.num.s, ...theme.tabular, color: theme.color.ink },
});
