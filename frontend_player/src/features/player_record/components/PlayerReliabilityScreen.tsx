/**
 * **Player reliability** — the ring, the word, and the record card's rows as it draws them
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2).
 *
 * The Player Score is out of a hundred, computed from what happened and never from opinions
 * or results — and the one number a player is most likely to be held back by without knowing
 * it. This screen is where they look: the score in 7.8's ring on a dark card at `ringLg`,
 * with the tone ladder's word beside it (*Reliable* from 90, *Holding* from 70, *Under the
 * bar* below — `scoreTone`'s three steps, said) and *Out of 100* under the word; then
 * `RecordCard` exactly as the sheet draws it — each strand's name and raw pair over its
 * meter, opponent variety, sportsmanship by players. No weights, no sentence under a row, no
 * card explaining what the number changes: the rows are the explanation.
 *
 * ## Absence is honest
 *
 * A player nothing has fallen due for has no `reliability` at all, and the screen says so in
 * one sentence rather than drawing a nought in a ring: there is no score, and that is not a
 * low one. The card is still drawn under it where the record has a variety or an opinion,
 * because those are different absences and do not move with the score's.
 *
 * ## The sportsmanship row draws what the record serves
 *
 * The figure and its count — *Sportsmanship, by players · 4,3 / 5 · 12 players* — the same row
 * a stranger reads on this player's record: ADR-0179 §5 serves the subject the figure and
 * retired the band from the wire (#468), the client read it from the moment the contract was
 * regenerated (#471), and the arm that once drew a band word is gone
 * ([#473](https://github.com/Raketa02/Raketa/issues/473)). Nothing here chooses: the row is
 * `RecordCard`'s, drawn here unchanged.
 */

import { useRouter } from 'expo-router';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { ShellScreen, YOU_COPY } from '@/features/shell/types';
import { recoveryMessage } from '@/shared/errors';
import { Button, ConfidenceRing, DarkCard, Note, theme } from '@/shared/ui';

import { scoreTone } from '../domain/scoreTone';
import { useOwnRecord } from '../hooks/useOwnRecord';

import { RecordCard } from './RecordCard';
import { RETRY_RECORD_LABEL } from './recordPresentation';
import {
  NOTHING_COUNTED,
  OUT_OF_100,
  PLAYER_RELIABILITY_TITLE,
  READING_OWN_RECORD,
  SCORE_TONE_WORD,
  scoreRingLabel,
} from './youRecordPresentation';

export function PlayerReliabilityScreen() {
  const router = useRouter();
  const { record } = useOwnRecord();
  const own = record.data;

  return (
    <ShellScreen
      eyebrow={YOU_COPY.groups.playing}
      title={PLAYER_RELIABILITY_TITLE}
      onBack={router.back}
    >
      {record.isPending ? (
        <ActivityIndicator accessibilityLabel={READING_OWN_RECORD} color={theme.color.muted} />
      ) : null}

      {record.error !== null ? (
        <View style={s.failure}>
          <Note variant="coral" accessibilityRole="alert">
            {recoveryMessage(record.error)}
          </Note>
          <Button
            label={RETRY_RECORD_LABEL}
            variant="secondary"
            onPress={() => void record.refetch()}
          />
        </View>
      ) : null}

      {own === undefined ? null : own.reliability === undefined ? (
        <Note variant="info">{NOTHING_COUNTED}</Note>
      ) : (
        <DarkCard style={s.ring}>
          <ConfidenceRing
            size="lg"
            value={own.reliability.playerScore}
            figure={String(own.reliability.playerScore)}
            accessibilityLabel={scoreRingLabel(own.reliability.playerScore)}
          />
          <View style={s.words}>
            <Text style={s.word}>{SCORE_TONE_WORD[scoreTone(own.reliability.playerScore)]}</Text>
            <Text style={s.scale}>{OUT_OF_100}</Text>
          </View>
        </DarkCard>
      )}

      {own === undefined ? null : (
        <RecordCard
          {...(own.reliability === undefined ? {} : { reliability: own.reliability })}
          {...(own.variety === undefined ? {} : { variety: own.variety })}
          {...(own.opinion === undefined ? {} : { opinion: own.opinion })}
        />
      )}
    </ShellScreen>
  );
}

const s = StyleSheet.create({
  failure: { gap: theme.space.sm },
  ring: { flexDirection: 'row', alignItems: 'center', gap: theme.space.lg },
  words: { flex: 1, gap: theme.space.xxs },
  word: { ...theme.type.cardTitle, color: theme.color.surface },
  scale: { ...theme.type.tiny, color: theme.color.onDarkTiny },
});
