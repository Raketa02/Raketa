/**
 * **Player reliability** — the figure in points with the band's word beside it, and the record
 * card's counts as it draws them
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2, [ADR-0195](../../../../../docs/adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md)
 * §1, [#660](https://github.com/Raketa02/Raketa/issues/660)).
 *
 * Points, from 100, computed from what happened and never from opinions or results. This screen
 * is where a player looks: the figure in 7.8's ring on a dark card at `ringLg`, with the band said
 * in full beside it — *Very high*, *High*, *Medium* or *Low reliability*, the server's band and
 * never this phone's thresholds — or *New* in its place, and *Out of 100* under the word; then
 * `RecordCard` exactly as the sheet draws it — the four counts, opponent variety, sportsmanship
 * by players. No weights, no meters, no ledger, and no card explaining what the number changes:
 * the counts are the account.
 *
 * ## A new player is told what New is, and nobody is told there is nothing
 *
 * Everyone has a figure from the start, so the sentence that once said *there is no score, and
 * that is not a low one* has no player left to say it to. What a new player gets instead is one
 * line under the ring — where the figure starts and what *New* means — and the counts as they
 * are served, noughts included.
 *
 * ## The filter sits between the figure and the counts, and the figure back under it
 *
 * `ReliabilityFilterCard` — *Play only with players of · Off | At least Medium | At least High*,
 * with *Your filter hides 2 of the 11 players in your groups* while it is on (ADR-0195 §6,
 * [#662](https://github.com/Raketa02/Raketa/issues/662)) — is drawn where the record serves a
 * filter, which is on your own record only. Under it, for a player somebody's filter keeps off a
 * court, one 5.4 `info` note: *Some players in your groups play only with High reliability or
 * above. At 75 you're dealt with everyone again.* It names nobody, and it is explanation and not
 * status, which is what `info` is for.
 *
 * ## The sportsmanship row draws what the record serves
 *
 * The figure and its count — *Sportsmanship, by players · 4,3 / 5 · 12 players* — the same row
 * a stranger reads on this player's record (ADR-0179 §5,
 * [#473](https://github.com/Raketa02/Raketa/issues/473)). Nothing here chooses: the row is
 * `RecordCard`'s, drawn here unchanged.
 */

import { useRouter } from 'expo-router';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { ShellScreen, YOU_COPY } from '@/features/shell/types';
import { recoveryMessage } from '@/shared/errors';
import { Button, ConfidenceRing, DarkCard, Note, theme } from '@/shared/ui';

import { useOwnRecord } from '../hooks/useOwnRecord';

import { RecordCard } from './RecordCard';
import { RETRY_RECORD_LABEL } from './recordPresentation';
import { ReliabilityFilterCard } from './ReliabilityFilterCard';
import {
  NEW_PLAYER_NOTE,
  OUT_OF_100,
  PLAYER_RELIABILITY_TITLE,
  READING_OWN_RECORD,
  backWithEveryoneLine,
  reliabilityWord,
  scoreRingLabel,
} from './youRecordPresentation';

export function PlayerReliabilityScreen() {
  const router = useRouter();
  const { record } = useOwnRecord();
  const own = record.data;
  const reliability = own?.reliability;
  const word = reliability === undefined ? undefined : reliabilityWord(reliability);

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

      {reliability === undefined ? null : (
        <DarkCard style={s.ring}>
          <ConfidenceRing
            size="lg"
            value={reliability.playerScore}
            figure={String(reliability.playerScore)}
            accessibilityLabel={scoreRingLabel(reliability.playerScore)}
          />
          <View style={s.words}>
            {word === undefined ? null : <Text style={s.word}>{word}</Text>}
            <Text style={s.scale}>{OUT_OF_100}</Text>
          </View>
        </DarkCard>
      )}

      {reliability?.isNew === true ? <Note variant="info">{NEW_PLAYER_NOTE}</Note> : null}

      {reliability?.filter === undefined ? null : (
        <ReliabilityFilterCard filter={reliability.filter} />
      )}

      {reliability?.backWithEveryone === undefined ? null : (
        <Note variant="info">{backWithEveryoneLine(reliability.backWithEveryone)}</Note>
      )}

      {own === undefined ? null : (
        <RecordCard
          counts={own.reliability.counts}
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
