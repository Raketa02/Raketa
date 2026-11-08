/**
 * **Rankings** — a ranking per sport, sorted by the level
 * ([#775](https://github.com/Raketa02/Raketa/issues/775); [ADR-0203](../../../../../docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md);
 * the rankings screens §2–§5; rankings 2–11).
 *
 * **The header** (§2): ‹ back to Home, *Rankings* with *Competitive games only* under it, small and
 * grey, and on the right **the deck's own sport pill** (`SportPillFrame`, #774), offering all four
 * sports, the reader's rated ones first. Switching sport is a new read of the page.
 *
 * **Under it, General** (§4, §5): the reader's place card — or the not-listed card in its place —
 * then the podium with three rows the reader sees, then the list on one white card, in pages of 50
 * with the floating *You · 212th* (#776, `RankingList`); *Nobody ranked in badminton yet* where
 * nobody is listed. The *General | Friends* switch is #777's.
 *
 * **The page opens on** the sport it was asked for — the trophy's, or the one a pass returns to —
 * else the deck's last, else padel (`useRankingsSport`), and draws nothing below the header until it
 * knows which.
 *
 * **A pull reads the page again** — every page drawn, the main read with them: places move whenever a
 * result settles anywhere in Raketa. While the first read is out nothing is drawn under the header
 * but the pull; a refused read says why with *Try again*, and a read waiting for a connection says
 * so. **Another sport is another page**, read from its top.
 *
 * **Any face, row or podium step opens the full record**, a stranger's too; the reader's own opens
 * their own (§6). Whose record is up is this screen's state — route-local, as Members holds it.
 *
 * **Pushed over Home, the Home column lit** (Q11): the shell lists `/rankings` inside Home's tab.
 */

import { router } from 'expo-router';
import { useState } from 'react';
import { RefreshControl, StyleSheet, Text, View } from 'react-native';

import { ReadFailure } from '@/features/groups/types';
import { PlayerRecordSheet, type RecordSubject } from '@/features/player_record/types';
import { offlineMessage } from '@/shared/errors';
import { Note, ScreenHeader, SportPillFrame, theme, TopSafeArea } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import { podiumOf, type RankedRow } from '../domain/ranking';
import { useGeneral } from '../hooks/useGeneral';
import { useRankingsSport } from '../hooks/useRankingsSport';

import { PlaceCard } from './PlaceCard';
import { PodiumSteps } from './PodiumSteps';
import { RankingList } from './RankingList';
import { RANKINGS_COPY, RANKINGS_PILL_WORDS, nobodyRankedLine } from './rankingsCopy';

export interface RankingsScreenProps {
  /** The sport the page was opened on — the trophy's, or a pass's way back. Absent: the deck's, or padel. */
  readonly sport?: Sport;
}

export function RankingsScreen({ sport: asked }: RankingsScreenProps) {
  const { sports, sport, pick } = useRankingsSport(asked);

  return (
    <TopSafeArea style={s.screen}>
      <SportPillFrame
        sports={sports}
        sport={sport}
        onPick={pick}
        words={RANKINGS_PILL_WORDS}
        header={(pill) => (
          <ScreenHeader
            onBack={() => router.back()}
            backLabel={RANKINGS_COPY.back}
            title={RANKINGS_COPY.title}
            subline={RANKINGS_COPY.subline}
            right={pill}
          />
        )}
      >
        {sport === undefined ? null : <GeneralPage key={sport} sport={sport} />}
      </SportPillFrame>
    </TopSafeArea>
  );
}

/**
 * General, for one sport: the card and the podium, then the list in pages — from the top, or around
 * the reader once the jump has landed.
 */
function GeneralPage({ sport }: { readonly sport: Sport }) {
  const general = useGeneral(sport);
  const { ranking } = general;
  const [reading, setReading] = useState<RecordSubject>();
  // A pull is the pull's own state, never the query's: a background refetch spins nothing, and a
  // pull spins until its read has landed, refused or not (ShellScreen's rule).
  const [pulling, setPulling] = useState(false);
  const pull = () => {
    if (pulling) return;
    setPulling(true);
    void general.reread().finally(() => setPulling(false));
  };

  const open = (row: RankedRow) =>
    setReading({ kind: row.isYou ? 'me' : 'player', playerId: row.playerId });
  const podium = ranking === undefined ? undefined : podiumOf(ranking.podium);

  const top =
    ranking === undefined ? (
      general.error !== null ? (
        <ReadFailure error={general.error} onRetry={general.retry} />
      ) : general.paused ? (
        <Note variant="amber">{offlineMessage('resumes')}</Note>
      ) : null
    ) : (
      <>
        {ranking.card === undefined ? null : <PlaceCard card={ranking.card} sport={sport} />}
        {ranking.listed === 0 ? (
          <Text testID="nobody-ranked" style={s.nobody}>
            {nobodyRankedLine(sport)}
          </Text>
        ) : podium === undefined ? null : (
          <PodiumSteps podium={podium} onOpen={open} />
        )}
      </>
    );
  const shownRows = ranking === undefined || ranking.listed === 0 ? [] : general.rows;

  return (
    <View style={s.page}>
      <RankingList
        window={general.window}
        rows={shownRows}
        header={
          <View style={s.header}>
            {general.atTheTop ? top : null}
            {general.earlierFailure === undefined ? null : (
              <ReadFailure
                error={general.earlierFailure.error}
                onRetry={general.earlierFailure.retry}
              />
            )}
          </View>
        }
        footer={
          general.laterFailure === undefined ? null : (
            <View style={s.footer}>
              <ReadFailure
                error={general.laterFailure.error}
                onRetry={general.laterFailure.retry}
              />
            </View>
          )
        }
        refreshControl={
          <RefreshControl
            refreshing={pulling}
            onRefresh={pull}
            tintColor={theme.color.muted}
            colors={[theme.color.muted]}
            progressBackgroundColor={theme.color.paper}
          />
        }
        onOpen={open}
        onStartReached={general.loadEarlier}
        onEndReached={general.loadLater}
        jump={general.jump}
      />

      {reading === undefined ? null : (
        <PlayerRecordSheet
          visible
          onClose={() => setReading(undefined)}
          subject={reading}
          sport={sport}
        />
      )}
    </View>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  page: { flex: 1 },
  // The card, the podium — or what stands in their place — above the rows, `sm` apart and from them.
  header: { gap: theme.space.sm, paddingBottom: theme.space.sm },
  footer: { paddingTop: theme.space.sm },
  nobody: {
    ...theme.type.rlLabel,
    color: theme.color.muted,
    textAlign: 'center',
    paddingVertical: theme.space.xl,
  },
});
