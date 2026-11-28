/**
 * **PLAYED WITH** — the result screen's card of the others on the game, each with where the reader
 * stands with them ([#754](https://github.com/Rakieta02/Rakieta/issues/754), PRD #743 story 15; the
 * friends screens §3; Q26). Designed, no mock.
 *
 * ```
 * PLAYED WITH
 * ┌───────────────────────────────────────────────┐
 * │ face  ewa.m              • Padel 2,60  friend │
 * │ face  magda.p            • Padel 2,66 [+ Add] │
 * │ face  ania.k             • Padel 2,68  request sent
 * └───────────────────────────────────────────────┘
 * ```
 *
 * **Members' rows with Members' pills** (§3): each row is `PersonRow` — the face, the name, the
 * game's sport over its dot and their Level — handed to `RowWithFriendEnd`, which puts **+ Add**,
 * *request sent*, **Accept** or *friend* on its right. **The pill acts and the rest of the row opens
 * the record**; a request asked here is `RESULT`'s, naming the game's group and sport, which the other
 * person's Home card says.
 *
 * **Hidden once every one of them is your friend** (`playedWithShown`), and after a For fun game
 * as after a Competitive one: the card asks nothing about the kind.
 *
 * ## The composer hands in the people, the record and the re-read
 *
 * The others' faces and Levels are the booking's seats, and where the reader stands with each is the
 * booking's `played_with`: both are `proposals`' read, which joins them (`playedWithOf`) into its own
 * `PlayedWithInput` — it imports nothing of this feature, so the route passes it here, and these
 * props agree with it structurally. The record
 * a row opens is `player_record`'s, which draws this feature's record button — so it is the
 * composer's to open (`onPerson`), as Home's request cards hand the face to the shell. And a pill
 * stays busy until the booking has read again (`reread`), so the row turns *request sent* on the
 * server's answer.
 */

import { StyleSheet, Text, View } from 'react-native';

import { sportLabel } from '@/features/onboarding/types';
import { Card, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import { playedWithShown, type PlayedWithPerson } from '../domain/friendList';
import type { Reread } from '../hooks/useFriendWrites';

import { FRIENDS_COPY, sportLevel } from './friendsCopy';
import { PersonRow } from './PersonRow';
import { RowWithFriendEnd } from './RowWithFriendEnd';

export interface PlayedWithCardProps {
  /** Everybody else on the game, in the read's order, each with the reader's relation to them. */
  readonly people: readonly PlayedWithPerson[];
  readonly sport: Sport;
  /** The game's group, which a request asked from the card names. */
  readonly groupId: string;
  /** A tap on the rest of a row: their record, the composer's to open. */
  readonly onPerson: (playerId: string) => void;
  /** The booking's re-read, which a pill awaits before it settles. */
  readonly reread: Reread;
}

export function PlayedWithCard({ people, sport, groupId, onPerson, reread }: PlayedWithCardProps) {
  const shown = playedWithShown(people);
  if (shown.length === 0) return null;

  const name = sportLabel(sport);
  return (
    <View style={s.section} testID="played-with">
      <Text style={s.heading} accessibilityRole="header">
        {FRIENDS_COPY.playedWith.heading}
      </Text>
      <Card style={s.card}>
        {shown.map((person, at) => (
          <View key={person.playerId} style={at > 0 ? s.divided : undefined}>
            <RowWithFriendEnd
              playerId={person.playerId}
              nickname={person.nickname}
              relation={person.relation}
              where={{ from: 'RESULT', groupId, sport }}
              reread={reread}
            >
              <PersonRow
                testID={`played-with-${person.playerId}`}
                playerId={person.playerId}
                nickname={person.nickname}
                {...(person.photoUrl === undefined ? {} : { photoUrl: person.photoUrl })}
                line={sportLevel(name, person.level)}
                sport={sport}
                onPress={() => onPerson(person.playerId)}
              />
            </RowWithFriendEnd>
          </View>
        ))}
      </Card>
    </View>
  );
}

const s = StyleSheet.create({
  // A new question under the score rather than another fact about it — the star card's own step.
  section: { marginTop: theme.space.lg, gap: theme.space.xs },
  // `eyebrow` labels a region being read, in `muted`, uppercase (the section heading).
  heading: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  card: { gap: theme.space.sm },
  // 5.3: `line2` folds one card into rows.
  divided: { borderTopWidth: 1, borderTopColor: theme.color.line2, paddingTop: theme.space.sm },
});
