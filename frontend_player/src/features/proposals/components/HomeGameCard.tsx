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
 * │ Paid · 30 zł · 28,55 zł back if you leave…│   the money line — none on a result state
 * │ [ Open game                        ]  ◯   │   the door, and the chat's bubble
 * └───────────────────────────────────────────┘
 * ```
 *
 * The Classic card's shell (`plans`' `GameCard`, 7.7's paging geometry, the footer on `marginTop:
 * auto`) with a booking's content, so one rail draws one language: **the body is one element with no
 * action** — its name the status, *new*, the sport, the facts, the money and whether the chat is open
 * (`homeCardLabel`) — and *Open game* is the one door, to the game's details (A4.1).
 *
 * ## The bubble says the chat is open, and is not a door
 *
 * A Home card has no chat door (A8; the mechanics §14.3: the chat is reached *only from the game
 * details*), and #556 asks for the bubble all the same — so it is drawn as what it can honestly be:
 * a mark that this game's room is open, not pressable and silent, its words in the body's name. It
 * is drawn where the room join finds a room and the status still has one (`chatIsOpen`). **Lit volt
 * when something is unread is owed**: the wire carries no unread count.
 */

import Feather from '@expo/vector-icons/Feather';
import { StyleSheet, Text, View } from 'react-native';

import { DarkCard, Button, theme } from '@/shared/ui';

import { peopleOn } from '../domain/deck';
import { moneyLineOf, type HomeGame } from '../domain/home';
import { gameDayOf } from '../domain/when';

import { CardTag } from './CardTag';
import { clubName, detailsDay, timeWords } from './deckPresentation';
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
  /** The game's room is open — the bubble. */
  readonly chat: boolean;
  /** The rail's card width — 7.7's paging geometry, handed down as the Classic card's is. */
  readonly width: number;
  readonly onOpen: () => void;
}

export function HomeGameCard({ game, now, fresh, chat, width, onOpen }: HomeGameCardProps) {
  const ink = STATUS_INK[game.status];
  const line = moneyLineOf(game, now);

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
          chat,
        })}
        style={s.body}
        testID={`home-game-${game.bookingId}`}
      >
        <View style={s.header}>
          <CardTag label={statusWord(game.status)} tone="grey" dot={ink} />
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
      </View>

      <View style={s.footer}>
        <Button
          label={COPY.openGame}
          variant={OPEN_GAME_VARIANT[game.status]}
          size="lg"
          onPress={onOpen}
          style={s.door}
        />
        {chat ? (
          <View style={s.bubble} testID="home-game-chat">
            <Feather
              name="message-circle"
              size={theme.size.tabIcon}
              color={theme.color.onDarkTiny}
              accessibilityElementsHidden
              importantForAccessibility="no"
            />
          </View>
        ) : null}
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
  // 7.7: the footer takes `marginTop: auto`, so footers align across cards of differing height.
  footer: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm, marginTop: 'auto' },
  door: { flex: 1 },
  // The bubble's box is the Classic card's door's width, so the two rails' footers line up.
  bubble: { minWidth: theme.size.minTouch, alignItems: 'center', justifyContent: 'center' },
});
