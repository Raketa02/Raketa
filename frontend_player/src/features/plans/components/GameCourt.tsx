/**
 * **The court inside a card that is about it** — 7.12 at `size.court.header`, with a name under
 * every face.
 *
 * The third composition over `Court`, beside `CourtMini` and `CourtBuild`, and a **third component
 * rather than a flag on either**: they share every number and no behaviour, which is the same
 * argument the other two were split on. What separates this one is the caption. `CourtMini` draws
 * none and says why — *"both screens this court appears on already print the handles in full and
 * unavoidably"* — and a Now card is the surface where that premise is false: it is a tag, a
 * figure, a line, a gloss and a footer, and **nowhere on it is anybody's name** unless the seats
 * carry it.
 *
 * **The seats are generated posters and need no new token.**
 * [ADR-0134](../../../../../docs/adr/0134-a-poster-is-a-fact-about-an-id.md) makes a poster a fact
 * about an id, which is why `seatFace.tsx` already draws your own seat from one — so the design's
 * coloured tile with initials **is** this app's poster plus 7.12's three-character caption. A seat
 * `users` can no longer answer for draws the unknown player's `?`, which is `playerName`'s and not
 * a case invented here.
 *
 * **A game's seat carries a handle and nothing else about the person in it** (ADR-0141), so the
 * caption prints no level: the record of an evening is not a card, and every figure on one would
 * be an as-of-now fact stapled to a game in the past.
 *
 * **Volt marks which seat is yours**, which is `CourtMini`'s meaning for it on a court with no
 * selection to confuse it with — one meaning per surface, because the two never appear together.
 *
 * **Nothing here announces.** The card around it is the accessibility element and its name states
 * the sport, so the court is drawn into a hidden subtree exactly as the pool header draws its own:
 * a `Court` summary heard beside a card label would be the same fact said twice.
 */

import type { Game } from '@/features/games/types';
import { SeatCaption, SeatFace, seatBox, type CourtFaceOccupant } from '@/features/play/types';
import { playerName } from '@/shared/formatting/playerName';
import { Court, courtSeatSize, theme, type SportKey } from '@/shared/ui';
import { StyleSheet, View } from 'react-native';

export interface GameCourtProps {
  readonly sport: SportKey;
  /** The court, in the order the challenge handed it over — never re-sorted here. */
  readonly seats: Game['seats'];
  /** The reader's own id, which is what turns one of the seats into *you*. */
  readonly playerId: string;
  /** `Court`'s required sentence. Drawn into a hidden subtree — see the module note. */
  readonly summary: string;
  /** The sport, named in text under the ground, which is what makes the tag's dot legal. */
  readonly caption: string;
}

export function GameCourt({ sport, seats, playerId, summary, caption }: GameCourtProps) {
  const size = courtSeatSize(theme.size.court.header);

  return (
    <View
      style={s.court}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <Court
        sport={sport}
        width={theme.size.court.header}
        summary={summary}
        caption={caption}
        // Every seat is a child, so the wrapper is the seat's slot and the caption hangs off it.
      >
        {seats.map((seat) => {
          const yours = seat.playerId === playerId;
          const occupant: CourtFaceOccupant = yours
            ? { kind: 'you', playerId: seat.playerId }
            : { kind: 'player', playerId: seat.playerId };

          return (
            <View key={seat.playerId} style={seatBox(size)}>
              <SeatFace size={size} occupant={occupant} ring={yours ? 'yours' : 'seated'} />
              <SeatCaption
                size={size}
                name={playerName(
                  yours
                    ? { kind: 'you' }
                    : seat.nickname === undefined
                      ? { kind: 'unknown' }
                      : { kind: 'player', nickname: seat.nickname },
                )}
              />
            </View>
          );
        })}
      </Court>
    </View>
  );
}

const s = StyleSheet.create({
  // The court is a fixed width and the card is not, so it is centred rather than stretched: a
  // drawing with a rule about its parts is sized by the part, never by the page.
  court: { alignSelf: 'center' },
});
