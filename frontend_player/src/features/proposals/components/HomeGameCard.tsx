/**
 * **One booked game on Home's rail** ([#556](https://github.com/Raketa02/Raketa/issues/556); the
 * screens A8; the mechanics §14.1) — a dark shell: the status and the sport · the court's facts on
 * the status's line, the faces beside them · the money line · *Open game*.
 *
 * ```
 * ┌───────────────────────────────────────────┐
 * │ ● Booked  New                      PADEL  │   the status (its dot the status's), new until opened
 * │ ▎WHERE  Bonarka Arena  Court 2   (P)(I)(B)│   the facts on the status's accent line, the others
 * │ ▎DAY    Saturday  3 Oct                   │
 * │ ▎TIME   16:00  until 17:00                │
 * │ 30 zł · free to leave until Fri 16:00     │   the money line — none on a result state
 * │ 2 of 3 friends in · waiting for ania.k    │   a friends game's seats, for its sender (#759)
 * │ [ Open game                        ] [◯]  │   the two doors: the details, and the chat
 * └───────────────────────────────────────────┘
 * ```
 *
 * The Classic card's shell (`plans`' `GameCard`, 7.7's paging geometry, the footer on `marginTop:
 * auto`) with a booking's content, so one rail draws one language: **the body is one element with no
 * action** — its name the status, *new*, the sport, the facts and the money (`homeCardLabel`) — and
 * the footer holds the card's two doors: *Open game*, to the game's details (A4.1), and the bubble.
 *
 * ## The bubble is a door into the room
 *
 * **Q100** (#619) made the bubble what Classic play's was: a 6.14 icon door (`ChatDoor`), spoken
 * *Open the chat* as the details' *Chat* is, that opens the game's room straight over Home — so
 * Back from that room is Home, and Back from a room opened from the details is the details. It is
 * drawn exactly where the room join finds a room and the status still has one (`chatIsOpen`), so
 * never on *Waiting for one payment*, a game gone back to filling (Q106) or *Called off*: the chat
 * opens when the game is booked. **Its count, and lit volt when something is
 * unread, are owed** with the details' *Chat · n* (F-HOME-21.1): the wire carries no unread count.
 */

import { StyleSheet, Text, View } from 'react-native';

import { DarkCard, Button, theme } from '@/shared/ui';

import { peopleOn } from '../domain/deck';
import { seatsLineOf } from '../domain/friendsGame';
import { moneyLineOf, shownStatus, type HomeGame } from '../domain/home';
import { gameDayOf } from '../domain/when';

import { CardTag } from './CardTag';
import { ChatDoor } from './ChatDoor';
import { clubName, detailsDay, timeWords } from './deckPresentation';
import { seatsLineWords } from './friendsGamePresentation';
import { GameFacts, type FactWords } from './GameFacts';
import { HOME_GAME_COPY } from './homeCopy';
import {
  OPEN_GAME_VARIANT,
  STATUS_INK,
  homeCardLabel,
  moneyWords,
  sportWords,
  statusWord,
  whereAside,
} from './homePresentation';
import { OthersFaces } from './OthersFaces';

const COPY = HOME_GAME_COPY;

export interface HomeGameCardProps {
  readonly game: HomeGame;
  /** The read's clock — the instant the money line and the day are folded against. */
  readonly now: number;
  /** Marked *new*: filled since the player last looked, and never opened. */
  readonly fresh: boolean;
  /**
   * **The bubble's door** — the game's room is open, and this opens it over Home; nothing, and no
   * bubble, while there is no room to open.
   */
  readonly onChat: (() => void) | undefined;
  /** The rail's card width — 7.7's paging geometry, handed down as the Classic card's is. */
  readonly width: number;
  readonly onOpen: () => void;
  /**
   * Removes a called-off game from this phone's Home. Offered only on a called-off card — the one
   * kind nothing else on Home can do anything about.
   */
  readonly onDismiss?: () => void;
}

export function HomeGameCard({
  game,
  now,
  fresh,
  onChat,
  width,
  onOpen,
  onDismiss,
}: HomeGameCardProps) {
  const status = shownStatus(game);
  const ink = STATUS_INK[status];
  const line = moneyLineOf(game, now);
  // The sender's own friends game, while a seat is not In (#759; the screens §6.3).
  const seatsLine = seatsLineOf(game, now);
  const seats = seatsLine === undefined ? undefined : seatsLineWords(seatsLine);

  const day = gameDayOf(game.startsAt, now);
  const when = day === undefined ? undefined : detailsDay(day, game.startsAt);
  const time = timeWords(game.startsAt);
  const where = whereAside(game, undefined);
  const facts: readonly FactWords[] = [
    {
      label: COPY.details.where,
      value: clubName(game),
      ...(where === undefined ? {} : { aside: where }),
    },
    ...(when === undefined ? [] : [{ label: COPY.details.day, ...when }]),
    { label: COPY.details.time, value: time.from, aside: time.until },
  ];

  return (
    <DarkCard style={[s.card, { width }]}>
      <View
        accessible
        accessibilityLabel={homeCardLabel({
          game,
          fresh,
          day,
          money: line,
          ...(seats === undefined ? {} : { seats }),
        })}
        style={s.body}
        testID={`home-game-${game.bookingId}`}
      >
        <View style={s.header}>
          <CardTag label={statusWord(status)} tone="grey" dot={ink} />
          {fresh ? <CardTag label={COPY.new} tone="volt" /> : null}
          <Text style={s.sport} numberOfLines={1}>
            {sportWords(game.sport, game.kind)}
          </Text>
        </View>

        <View style={s.court}>
          <View style={s.facts}>
            <GameFacts facts={facts} accent={ink} size="card" />
          </View>
          <OthersFaces people={peopleOn(game)} />
        </View>

        {line === undefined ? null : <Text style={s.line}>{moneyWords(line)}</Text>}
        {seats === undefined ? null : <Text style={s.seats}>{seats}</Text>}
      </View>

      <View style={s.footer}>
        <Button
          label={COPY.openGame}
          variant={OPEN_GAME_VARIANT[status]}
          size="lg"
          onPress={onOpen}
          style={s.door}
        />
        {onChat === undefined ? null : (
          <ChatDoor onPress={onChat} testID={`home-game-chat-${game.bookingId}`} />
        )}
        {status !== 'CALLED_OFF' || onDismiss === undefined ? null : (
          <Button label={COPY.removeGame} variant="secondary" size="lg" onPress={onDismiss} />
        )}
      </View>
    </DarkCard>
  );
}

const s = StyleSheet.create({
  card: { gap: theme.space.md },
  body: { gap: theme.space.md },
  header: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  // `marginLeft: auto` rather than `space-between`, so the word stays right however many tags.
  sport: {
    ...theme.type.eyebrow,
    color: theme.color.onDarkEyebrow,
    textTransform: 'uppercase',
    marginLeft: 'auto',
    flexShrink: 1,
  },
  court: { flexDirection: 'row', alignItems: 'flex-start', gap: theme.space.md },
  facts: { flex: 1 },
  line: { ...theme.type.tiny, color: theme.color.onDarkTiny },
  // The seats are the state to watch, so they read in the card's own white, under the money.
  seats: { ...theme.type.tiny, color: theme.color.surface },
  // 7.7: the footer takes `marginTop: auto`, so footers align across cards of differing height.
  footer: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm, marginTop: 'auto' },
  door: { flex: 1 },
});
