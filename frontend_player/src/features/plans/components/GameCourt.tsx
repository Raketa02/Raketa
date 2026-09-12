/**
 * **The court inside the Now card** — 7.12 at `size.court.card`, with a face and three letters
 * in every seat ([#413](https://github.com/Raketa02/Raketa/issues/413)).
 *
 * The third composition over `Court`, beside `CourtMini` and `CourtBuild`, and a **third component
 * rather than a flag on either**: they share every number and no behaviour, which is the same
 * argument the other two were split on. What separates this one is the caption. `CourtMini` draws
 * none and says why — *"both screens this court appears on already print the handles in full and
 * unavoidably"* — and a Now card is the surface where that premise is false: it is a tag, a sport
 * word, three slots and a footer, and **nowhere on it is anybody's name** unless the seats carry
 * it.
 *
 * ## The caption is three letters on every seat, yours included
 *
 * The seat that is yours used to read `you`, on `playerName`'s own arm for a sentence addressed to
 * its reader. On this court the **ring is the mark** — 2pt `volt`, `CourtMini`'s meaning for it on
 * a court with no selection to confuse it with — and a caption saying it again is the same fact
 * twice under one face. So every seat draws the first three letters of its handle, and the one
 * with the ring is you. `?` for a seat `users` can no longer answer for is `playerName`'s and not a
 * case invented here. The **spoken** name is unchanged: the card around this court is the
 * accessibility element, and its label says the sport and the slots.
 *
 * ## The faces are the room's, and the poster is the fallback
 *
 * A game's seat carries a handle and nothing else about the person in it (ADR-0141), so the face
 * comes from the **join** — the conversation rows the rail already fetches carry every member's
 * `photoUrl`, and the rail hands each card the map for its own room. A seat whose id the map has
 * nothing for draws the generated poster, which
 * [ADR-0134](../../../../../docs/adr/0134-a-poster-is-a-fact-about-an-id.md) makes a fact about the
 * id — so no room, no faces, posters drawn, and nothing here can tell the two apart or needs to.
 *
 * **Every seat is handed as a `player`, your own included.** `SeatFace`'s `you` occupant exists
 * for the builder, where your seat is drawn before anything has answered for it and nothing can
 * carry your photograph; here the room carries it, so your seat is a person with a face like the
 * other three, and *which one is you* is the ring's to say — the court decides the ring, as it
 * always has.
 *
 * ## An open seat is drawn empty, and it is the builder's empty seat
 *
 * A seat somebody left is a seat — `player_id: null`, never dropped
 * ([ADR-0162](../../../../../docs/adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md))
 * — so the court keeps its size and the gap is drawn where the person was: `SeatFace`'s `empty`
 * occupant under the dashed `empty` ring `CourtBuild` draws for a seat nobody is in, with no plus
 * (nothing here is pressable), no caption (there is no handle to cut) and no `yours` ring (it is
 * nobody's). `CourtMini` draws an unfilled seat as nothing at all, and the reason does not
 * transfer: that court's summary says how many seats are filled, and this one's card names the
 * errand — *Needs a player* — and draws the seat the errand is about.
 *
 * ## No sport caption on the ground
 *
 * The court used to carry the sport's name in its bottom band, because a tag's dot was the
 * sport's and a dot is legal only beside its name. The dot is the stage's now and the sport is the
 * **word** in the card's header, so a caption here would be the same word twice on one card, and
 * the ground is left to the faces. The court still says the format — four squares is a four.
 *
 * **Nothing here announces.** The card around it is the accessibility element and its name states
 * the sport, so the court is drawn into a hidden subtree exactly as the pool header draws its own:
 * a `Court` summary heard beside a card label would be the same fact said twice.
 */

import type { Game } from '@/features/games/types';
import { SeatCaption, SeatFace, seatBox } from '@/features/play/types';
import { playerName } from '@/shared/formatting/playerName';
import { Court, courtSeatSize, theme, type SportKey } from '@/shared/ui';
import { StyleSheet, View } from 'react-native';

export interface GameCourtProps {
  readonly sport: SportKey;
  /** The court, in the order the challenge handed it over — never re-sorted here. */
  readonly seats: Game['seats'];
  /** The reader's own id, which is what puts the ring on one of the seats. */
  readonly playerId: string;
  /** Each seat's photograph by player id, from the room. Absent is a poster, never an error. */
  readonly faces: ReadonlyMap<string, string>;
  /** `Court`'s required sentence. Drawn into a hidden subtree — see the module note. */
  readonly summary: string;
}

export function GameCourt({ sport, seats, playerId, faces, summary }: GameCourtProps) {
  const size = courtSeatSize(theme.size.court.card);

  return (
    <View
      style={s.court}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <Court sport={sport} width={theme.size.court.card} summary={summary}>
        {seats.map((seat, at) =>
          seat.playerId === undefined ? (
            // The open seat: a dashed outline where the person was, and nothing in it. Keyed by
            // its place on the court, because two people may leave and neither seat has an id.
            <View key={`open-${at}`} style={seatBox(size)}>
              <SeatFace size={size} occupant={{ kind: 'empty' }} ring="empty" />
            </View>
          ) : (
            // Every seat is a child, so the wrapper is the seat's slot and the caption hangs off it.
            <View key={seat.playerId} style={seatBox(size)}>
              <SeatFace
                size={size}
                occupant={{
                  kind: 'player',
                  playerId: seat.playerId,
                  photoUrl: faces.get(seat.playerId),
                }}
                ring={seat.playerId === playerId ? 'yours' : 'seated'}
              />
              <SeatCaption
                size={size}
                name={playerName(
                  seat.nickname === undefined
                    ? { kind: 'unknown' }
                    : { kind: 'player', nickname: seat.nickname },
                )}
              />
            </View>
          ),
        )}
      </Court>
    </View>
  );
}

const s = StyleSheet.create({
  // The court is a fixed width and the card is not, so it is placed rather than stretched: a
  // drawing with a rule about its parts is sized by the part, never by the page.
  court: { alignSelf: 'flex-start' },
});
