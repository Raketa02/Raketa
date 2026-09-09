/**
 * **`CHALLENGES` on the Chats tab** — every challenge you hold a seat in that is still being
 * arranged, yours and theirs, plus every one that ended recently.
 *
 * A section composed by the tab rather than a screen of its own, exactly as `GamesSection` is
 * composed on Now and `PlayIntentsSection` on You: the tab owns its own sentences and nothing
 * that is drawn under it.
 *
 * **No count on the heading.** The section had to widen to hold a challenge you *sent* — which
 * is drawn nowhere else in the app — and a count here would then disagree with the badge, which
 * counts only what is addressed to you ([#326](https://github.com/Raketa02/Raketa/issues/326)
 * §6). **The badge is the only number on this screen**, and two numbers meaning different things
 * on one screen is that record's own named failure.
 *
 * **The order is `challengeInbox`'s and is not re-derived here** — whose turn it is, then the
 * clock — so the thing the badge counts is the thing at the top of the list.
 *
 * **The empty line is the tab's rather than this feature's.** It says what lands on this
 * *screen*, and the screen is the shell's; what is this feature's is the heading, which names
 * its own content. Neither may assert that nothing is happening: a send lands here now.
 */

import { StyleSheet, Text, View } from 'react-native';

import { recoveryMessage } from '@/shared/errors';
import { Note, theme } from '@/shared/ui';

import { useChallengeInbox } from '../hooks/useChallenges';

import { ChallengeRow } from './ChallengeRow';
import { CHALLENGES_HEADING } from './challengePresentation';

export interface ChallengesSectionProps {
  /**
   * What this section says when it holds nothing — one present-tense line naming the act, per
   * [10.1](../../../../docs/design-system.md#101-screen-structure).
   */
  readonly empty: string;
}

export function ChallengesSection({ empty }: ChallengesSectionProps) {
  const { data, error, playerId, rows } = useChallengeInbox();

  // *The list has landed and the reader is known.* Both, because `useCurrentUser` is seeded by
  // bootstrap and answers first: gating the empty line on the reader alone would draw *nothing
  // has been sent to you* in the gap before the list arrives, which is the flash 10.1's no-spinner
  // rule is about from the other side.
  const answered = data !== undefined && playerId !== undefined;

  return (
    <View style={s.section}>
      <Text style={s.heading} accessibilityRole="header">
        {CHALLENGES_HEADING}
      </Text>

      {/* A read that failed is worth a sentence rather than an emptiness: a section that
          vanished on an error would be indistinguishable from having nothing in it, which is
          the one thing an inbox must not be. */}
      {error !== null ? (
        <Note variant="coral" accessibilityRole="alert">
          {recoveryMessage(error)}
        </Note>
      ) : null}

      {/* A read still in flight draws **nothing at all**: 10.1 forbids a spinner in this slot,
          and flashing the empty line before the list lands would tell a player nothing was sent
          to them a moment before the rows arrive. */}
      {error === null && answered && rows.length === 0 ? (
        <Text style={s.empty}>{empty}</Text>
      ) : null}

      {playerId === undefined
        ? null
        : rows.map((challenge) => (
            <ChallengeRow key={challenge.challengeId} challenge={challenge} playerId={playerId} />
          ))}
    </View>
  );
}

const s = StyleSheet.create({
  section: { gap: theme.space.sm, marginTop: theme.space.lg },
  // 3.3 as amended: a section heading is `eyebrow` / `muted` / uppercase, and `h2` titles a card.
  heading: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  empty: { ...theme.type.tiny, color: theme.color.muted },
});
