/**
 * **`PLAYERS`** — one row per seat, the face, the whole handle and the Level under it, and a tap
 * that opens the record ([#415](https://github.com/Raketa02/Raketa/issues/415),
 * [7.19](../../../../docs/design-system.md#719-the-people-list)).
 *
 * ```
 * PLAYERS                                           eyebrow
 * (TK) tomek.p (you)                                face 38 · cardTitle
 *      2,71 · Established · likely 2,55 – 2,87 · 74% sure     num.xs, muted, tabular
 * (ZB) zofia.b
 *      …
 * Tap anyone for their record — level, form and how  tiny, muted
 * they behave. Counted by the system; nobody writes
 * text about people here.
 * ```
 *
 * ## The rows are the court's and the Levels are the pairing's
 *
 * The seats come off `GET /games` — a handle and nothing else (ADR-0141) — and the row under
 * each handle comes off `GET /games/{game_id}/pairing`, which names whoever holds a rating in the
 * sport and nobody else (ADR-0161 §4). So the card is always drawn: it does not depend on the
 * forecast, and a seat the pairing has no row for — unrated, or the read refused or not landed —
 * draws the handle with nothing under it. **No chip on anybody.** Mock 4's *proposed it* / *in*
 * are not built, and a row carries the four figures a record prints and no claim beyond them.
 *
 * **Your side first — you, then your partner — then the other side** (`courtForReader`): a list
 * of people is read from the reader outward, whatever order the challenge seated the court in.
 *
 * ## An open seat is a row with nobody in it
 *
 * A seat somebody left is still a seat (ADR-0162, #411 rule 6), so it keeps its row in the
 * reader's order: an empty face — `SeatFace`'s `empty` occupant under Play's dashed ring, the
 * same drawing the Now card's court uses for it — the words `Open seat` where the handle would
 * be, no level row (the pairing names whoever holds a rating, and nobody holds this seat), and
 * **not a button**: there is no record to open for nobody, and a row that could be pressed
 * would promise one. It is one plain element, named by its own words.
 *
 * ## The face is the room's, and it is the Chats row's size
 *
 * A game's seat carries no photograph, so the face comes off the same join the Now card above
 * draws its court from — the room's members, handed down by the composition — and a seat the
 * map has nothing for draws the generated poster, a fact about the id (ADR-0134). The box is 38pt
 * because that is the row face the Chats tab's prototype published and **the only row face any
 * device in this repository has drawn**; both Chats rows hold that number in a geometry file of
 * their own and argue against `shared/ui` owning it (#338 §5), and this card is the third caller
 * those files said would force the question. It is spelled here rather than answered here: where
 * a face's home is belongs to a change about faces, not to the pairing.
 *
 * ## Tap, not hold, and the row is the button
 *
 * The design's *press and hold anyone* is refused on #285's argument — a hold has no affordance,
 * no announcement and no equivalent in the accessibility API — and **tap** is the gesture: the
 * whole row is one `button` named for the record it opens (`recordLabel`), dimmed on press as
 * 6.6's tick-box row is, because the row is the target — and lifted to 6.5's 44 by
 * `hit.peopleRow`, since a 38pt face is the row's whole height and the card's step between rows
 * belongs to the card, not to the press. It opens `PlayerRecordSheet` for that
 * player — the read behind it admits somebody you share a game with, so there is no backend work
 * behind the tap — with the sport the reader arrived from and nothing else: no search stands
 * behind this screen, so no distance, no overlap and no pairing row. Your own row opens your own
 * record, retitled, which is the sheet's own rule read off `kind: 'me'`.
 *
 * ## Three kinds of element
 *
 * The eyebrow is a `header`; each row is a `button` whose name is the record it opens and whose
 * hint is the level row, so a listener hears what the sighted reader sees under the handle; the
 * footer is one plain sentence. The face announces nothing (it is a picture of somebody the row
 * already names) and the sheet takes focus on its title when it opens.
 */

import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { SeatFace } from '@/features/play/types';
import { PlayerRecordSheet, type RecordSubject } from '@/features/player_record/types';
import { Card, PlayerPhoto, theme } from '@/shared/ui';

import type { Game, GameSeat } from '../domain/game';
import { courtForReader, type Pairing } from '../domain/pairing';

import {
  OPEN_SEAT,
  PLAYERS,
  PLAYERS_FOOTER,
  playerRowName,
  recordLabel,
  seatLevelLine,
} from './gamePresentation';

/**
 * The face, in points — the Chats row's number, spelled here for the reason the module note gives
 * and not moved: a third caller is the signal the two geometry files named, and the answer is
 * theirs to give.
 */
const FACE = 38;

export interface PlayersCardProps {
  readonly game: Game;
  /** The reader's own id — which seat is yours is a join and not a rule (ADR-0141). */
  readonly playerId: string;
  /** The pairing beside the game, or nothing: the rows stand either way, and the Levels do not. */
  readonly pairing: Pairing | undefined;
  /** Each seat's photograph by player id, from the room. Absent is a poster, never an error. */
  readonly faces: ReadonlyMap<string, string>;
}

export function PlayersCard({ game, playerId, pairing, faces }: PlayersCardProps) {
  /**
   * Whose record is open, or nobody's. **Route-local**, on the builder's own argument: the sheet
   * reads no global state and is gone the moment the screen pops, and a state carrying an
   * optional subject would be a sheet that could be opened about nobody.
   */
  const [reading, setReading] = useState<RecordSubject>();

  const rows = courtForReader(game.seats, playerId);
  /** The pairing's row for a seat, or nothing for somebody unrated. */
  const pairingRowOf = (seat: GameSeat) =>
    pairing?.seats.find((row) => row.playerId === seat.playerId);

  return (
    <Card style={s.card}>
      <Text accessibilityRole="header" style={s.eyebrow}>
        {PLAYERS}
      </Text>

      <View style={s.rows}>
        {rows.map((seat, at) => {
          if (seat.playerId === undefined) {
            // Keyed by its place in the reader's order: two people may leave, and neither seat
            // has an id to key on.
            return (
              <View key={`open-${at}`} style={s.row} accessible accessibilityLabel={OPEN_SEAT}>
                <SeatFace size={FACE} occupant={{ kind: 'empty' }} ring="empty" />
                <View style={s.words}>
                  <Text style={s.handle} numberOfLines={1}>
                    {OPEN_SEAT}
                  </Text>
                </View>
              </View>
            );
          }

          const { playerId: who } = seat;
          const person = {
            ...(seat.name === undefined ? {} : { name: seat.name }),
            yours: who === playerId,
          };
          const row = pairingRowOf(seat);
          const line = row === undefined ? undefined : seatLevelLine(row);

          return (
            <Pressable
              key={who}
              accessibilityRole="button"
              accessibilityLabel={recordLabel(person)}
              {...(line === undefined ? {} : { accessibilityHint: line })}
              onPress={() => setReading({ kind: person.yours ? 'me' : 'player', playerId: who })}
              hitSlop={theme.hit.peopleRow}
              // 6.6: the row is the target, so the row dims — the tick-box row's rule.
              style={({ pressed }) => [s.row, pressed ? s.rowPressed : undefined]}
            >
              <PlayerPhoto
                playerId={who}
                {...(faces.get(who) === undefined ? {} : { photoUrl: faces.get(who) })}
                box={{ kind: 'face', size: FACE }}
              />
              <View style={s.words}>
                <Text style={s.handle} numberOfLines={1}>
                  {playerRowName(person)}
                </Text>
                {line === undefined ? null : (
                  <Text style={s.level} numberOfLines={1}>
                    {line}
                  </Text>
                )}
              </View>
            </Pressable>
          );
        })}
      </View>

      <Text style={s.footer}>{PLAYERS_FOOTER}</Text>

      {/* No `returnFocusTo`, on the builder's precedent: up to four rows open the same sheet, so
          there is no one control to return to. */}
      {reading === undefined ? null : (
        <PlayerRecordSheet
          visible
          onClose={() => setReading(undefined)}
          subject={reading}
          sport={game.sport}
        />
      )}
    </Card>
  );
}

const s = StyleSheet.create({
  card: { gap: theme.space.sm },
  eyebrow: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  rows: { gap: theme.space.sm },
  // 38 tall — the face — and lifted to 44 by `hit.peopleRow` on the Pressable, not by padding:
  // the mock's rows sit at the card's step, and padding would move the step.
  row: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  rowPressed: { opacity: 0.7 },
  words: { flex: 1, gap: theme.space.xxs },
  handle: { ...theme.type.cardTitle, color: theme.color.ink },
  // Mono for the whole line, not only its numbers: three of its four clauses are figures, and
  // 1.4's tabular rule is what keeps four rows' Levels in one column.
  level: { ...theme.num.xs, ...theme.tabular, color: theme.color.muted },
  footer: { ...theme.type.tiny, color: theme.color.muted },
});
