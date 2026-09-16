/**
 * **The ended court** — every seat with somebody in it, and what each person did
 * ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
 * §7): *You · in*, *Javier Fabregat · left*, *Arnau Gallego · said no*, *Oscar Bertran · called
 * it off*. Drawn under the row's sentence on the challenge screen's `ended` arm, and nothing on it
 * is pressable — the arm has no fill, no chat door, no leave and no remove, because nothing on an
 * ended court is an act the server would accept.
 *
 * ## One card, one fold per seat, and the word is the fact
 *
 * A `Card` — 5.1's bounded surface — with a row per person: their face, their whole name and one
 * word, folded from each other by `line2` hairlines because they are one thing. The face is
 * `PlayerPhoto` at the Chats row's size, always the poster on this read (the detail carries a
 * card's photograph only where a card is drawn, and an ended court draws none). The word is in
 * the colour meaning picks — `red` for *left* and *called it off*, 1.3's *ended badly*; `mintInk`
 * for *in*, settled; `muted` for a no and a lapse — and never colour alone: the word is the fact,
 * and the colour is what the eye lands on first.
 *
 * ## One element per seat, and the row is what it says
 *
 * §20.1: everything with no action of its own merges into the nearest action above it, and there
 * is none here — so each seat is one element named by its own line, which is what the eye reads
 * too, and a listener moving down the court hears *You, in* · *Javier Fabregat, left* in order.
 */

import { StyleSheet, Text, View } from 'react-native';

import { playerName } from '@/shared/formatting/playerName';
import { Card, PlayerPhoto, theme } from '@/shared/ui';

import type { SeatDid, SeatWord } from '../domain/challengeDetail';

import { SEAT_WORD, THE_COURT_HEADING, seatDidLine } from './challengeDetailPresentation';
import { ROW_FACE } from './challengeRowGeometry';

export interface EndedCourtProps {
  readonly court: readonly SeatDid[];
}

export function EndedCourt({ court }: EndedCourtProps) {
  return (
    <View style={s.block}>
      <Text style={s.heading}>{THE_COURT_HEADING}</Text>

      <Card>
        {court.map((seat, at) => (
          <View
            key={seat.playerId}
            accessible
            accessibilityLabel={seatDidLine(seat.who, seat.did)}
            style={[s.seat, at === 0 ? undefined : s.folded]}
          >
            <PlayerPhoto playerId={seat.playerId} box={{ kind: 'face', size: ROW_FACE }} />
            <Text style={s.name} numberOfLines={1}>
              {playerName(seat.who)}
            </Text>
            <Text style={[s.did, DID_INK[seat.did]]}>{SEAT_WORD[seat.did]}</Text>
          </View>
        ))}
      </Card>
    </View>
  );
}

/**
 * The word's ink, by meaning — a `Record` over the union so a sixth word cannot arrive without
 * deciding its colour. Leaving a game is 1.3's *ended badly*; being in is settled; a no, a lapse
 * and a seat still deciding when the court closed are quiet facts about a court that never
 * became one, or stopped being one.
 */
const DID_INK: Readonly<Record<SeatWord, { readonly color: string }>> = {
  in: { color: theme.color.mintInk },
  left: { color: theme.color.red },
  'said-no': { color: theme.color.muted },
  'ran-out': { color: theme.color.muted },
  asked: { color: theme.color.muted },
};

const s = StyleSheet.create({
  block: { gap: theme.space.xs },
  heading: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  seat: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  // A fold inside one thing: `line2`, never `line`, which bounds a thing.
  folded: {
    borderTopWidth: 1,
    borderTopColor: theme.color.line2,
    marginTop: theme.space.sm,
    paddingTop: theme.space.sm,
  },
  name: { ...theme.type.cardTitle, color: theme.color.ink, flex: 1 },
  did: { ...theme.type.tiny },
});
