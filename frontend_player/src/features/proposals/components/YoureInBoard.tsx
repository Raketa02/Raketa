/**
 * **A group's You’re in tab** — the reader's own live yeses in this group and sport, on games still
 * filling ([#557](https://github.com/Raketa02/Raketa/issues/557), a tab of its own since
 * [#847](https://github.com/Raketa02/Raketa/issues/847); the screens A3, A3.2; split mock 2;
 * mock 13; the mechanics §10.2).
 *
 * ```
 * ┏ Padel · Saturday 15:00 ━━━━━━━━━━━━━━━━━━━━━━┓   mint
 * ┃ Bonarka Arena · book by Sat 13:00            ┃
 * ┃ [TK] [  ] [  ] [  ]              [ Withdraw ] ┃
 * ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
 *                                    [ + Post a game ]   the page's, floating over this tab alone
 * ```
 *
 * **Its read is its own**: the live yeses (`yesesIn`) — picks, challenges and posts, never a rescue,
 * which goes straight to Home — in the list's order, soonest first, each row reading its own game's
 * details for the squares. While nothing is drawn yet, the spinner (*Reading You’re in*); a read held
 * offline says it resumes, and one refused says why with the retry. None of it touches Fill in. The
 * read starts as the page opens, for the tab's badge (`useYoureInBadge`), so the tab usually opens
 * already read.
 *
 * **No heading**: the tab's name does that job. **Empty, it is one of two things** (split Q3):
 * - the group's starting card the page hands in (`empty`), **only once Fill in's read has said there
 *   is nothing too** — never as a first frame, so while Fill in's read is on its way, the spinner;
 * - otherwise one line, *You haven’t said yes to a game here yet* — while Fill in has a seat, and
 *   while Fill in could not say, since the starting card needs both reads.
 *
 * Fill in's read is the same query the Fill in tab and its badge read, so asking whether it is empty
 * costs no request. **Withdraw** takes a yes back in place: the row leaves and the tab stays, on its
 * empty state if it was the last.
 *
 * **What it draws is seen while it is on screen** (ADR-0208, #849): every yes here is marked seen by
 * its proposal whenever the rows change while the page is in view, with no record's sheet and
 * nothing of the fill's over it — a post landing here, a pull, a yes withdrawn — and one that
 * arrives while a game's details are
 * pushed over the page is seen when the page is uncovered. The tab bar's badge counts the rest.
 *
 * A row's upper block opens its game still filling (A4.2). A held poster opens that player's record,
 * as a sibling of the rows so they are hidden from a listener while the sheet is up.
 */

import { router } from 'expo-router';
import { useState, type ReactNode } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { PlayerRecordSheet } from '@/features/player_record/types';
import { behindOverlay, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { DeckPerson } from '../domain/deck';
import { yesIds, yesesIn, youreInEmpty } from '../domain/fillIn';
import { useFill } from '../hooks/useFill';
import { useSeatsToFill } from '../hooks/useFillIn';
import { useLiveYeses } from '../hooks/useLiveYeses';
import { useSeeRows } from '../hooks/useSeenRows';

import { FILL_IN_COPY } from './fillInCopy';
import { HeldRead, isHeld } from './HeldRead';
import { gameRoute } from './proposalRoutes';
import { YoureInRow } from './YoureInRow';

const COPY = FILL_IN_COPY;

export interface YoureInBoardProps {
  readonly groupId: string;
  readonly sport: Sport;
  /** What the tab draws once neither tab has a row — the group's starting card. */
  readonly empty: ReactNode;
  /** Whether the page is the screen in view — nothing pushed over it (`useScreenInView`). */
  readonly inView: boolean;
}

export function YoureInBoard({ groupId, sport, empty, inView }: YoureInBoardProps) {
  const live = useLiveYeses();
  // Fill in's read, asked only whether it is empty. Its refusal is drawn on Fill in, which reads it
  // again when that tab opens; this tab opening never re-asks a refused one.
  const rescues = useSeatsToFill(groupId, sport, { retryOnMount: false });
  const [reading, setReading] = useState<DeckPerson | undefined>(undefined);
  const fill = useFill();
  // What the tab draws is seen while it is on screen — the page in view, and no record's sheet and
  // nothing of the fill's over it. Everything the tab counts is drawn, so the two are one list.
  const here =
    live.data === undefined ? undefined : yesIds(yesesIn(live.data.yeses, groupId, sport));
  useSeeRows(
    groupId,
    sport,
    'youreIn',
    here === undefined ? undefined : { onScreen: here, counted: here },
    inView && reading === undefined && fill.over === 'none',
  );

  const drawn = (): ReactNode => {
    const spinner = (
      <ActivityIndicator accessibilityLabel={COPY.readingYoureIn} color={theme.color.muted} />
    );
    if (live.data === undefined) return isHeld(live) ? <HeldRead read={live} /> : spinner;
    const yeses = yesesIn(live.data.yeses, groupId, sport);
    if (yeses.length === 0) {
      switch (youreInEmpty(rescues.seats, isHeld(rescues.read))) {
        case 'startingCard':
          return empty;
        case 'line':
          return <Text style={s.empty}>{COPY.noYeses}</Text>;
        case 'waiting':
          return spinner;
      }
    }
    // The read's clock: the instant the list was received, as You › Payments reads its rows.
    const now = live.dataUpdatedAt;
    return yeses.map((yes) => (
      <YoureInRow
        key={yes.proposalId}
        yes={yes}
        now={now}
        onOpen={() => router.push(gameRoute(groupId, yes.proposalId, yes.sport, yes.kind))}
        onHold={setReading}
      />
    ));
  };

  return (
    <>
      <View style={s.board} {...behindOverlay(reading !== undefined)}>
        {drawn()}
      </View>

      {reading === undefined ? null : (
        <PlayerRecordSheet
          visible
          onClose={() => setReading(undefined)}
          subject={{ kind: 'player', playerId: reading.playerId }}
          sport={sport}
          groupId={groupId}
        />
      )}
    </>
  );
}

const s = StyleSheet.create({
  // Room under whatever the tab draws — rows, the starting card's doors, a refusal's retry — for the
  // floating *+ Post a game*, which sits over the page's corner.
  board: { gap: theme.space.sm, paddingBottom: theme.size.btnLg + theme.space.lg },
  // 10.1's empty state: one line of `tiny` in `muted`.
  empty: { ...theme.type.tiny, color: theme.color.muted },
});
