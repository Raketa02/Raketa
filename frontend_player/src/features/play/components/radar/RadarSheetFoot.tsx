/**
 * **The record sheet's foot, on the radar** — *Not today* and *Let's play*, or what already
 * stands between the reader and the person on the card
 * ([ADR-0174](../../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §4, [`the-radar.md`](../../../../../../docs/specs/matchmaking/the-radar.md) §5,
 * `the-words.md` §26).
 *
 * ## It reads the relation, and the fold is the domain's
 *
 * Five facts from four places: the row's own admitting code, the reader's outgoing and mutual
 * lists (`useInterest`), the reader's challenge list (`useCourtWith`, the challenges feature's
 * own pair rule) and, for a court, the room it opened (`useChatDoor`, the conversations
 * feature's join). Which of the five feet they earn is `domain/standingRelation`'s and not
 * decided here — a component holding the precedence is one refactor from two buttons over a
 * match. What this file owns is the drawing:
 *
 * | relation | the foot |
 * | --- | --- |
 * | open | **Not today** · **Let's play** — `secondary` and `primary`, the swipe's reading order |
 * | liker | *Wants to play you*, the volt tag, above the two |
 * | said yes | the plain *You said yes* tag beside **Not today** |
 * | matched | *You're matched*, and **Open the chat** where the court has a room |
 * | court | the court's own line — the Chats row's sentence, `standingLine` — and no buttons |
 *
 * ## What it does not decide
 *
 * **The cap.** A yes at the ceiling on a stranger is withheld before it is sent, by the deck's
 * own rule (`domain/yesBudget`), and the pane answers it as the deck does — the sentence — so
 * the two surfaces cannot disagree about who may fly. The foot hands the press up and the pane
 * decides. **The closing.** Every press closes the sheet first, and the pane owns the sheet.
 * **The chat's route.** The pane pushes it, after the sheet is down: a `Modal` stays over a
 * pushed screen, so the door leads nowhere until the sheet has gone.
 *
 * ## Composed at the surface, as the game screen's chat door is
 *
 * `challenges` may not know `conversations` exists (ADR-0146), so the court's id crosses one
 * seam and the room's id the other, and this — the surface — is where they meet (ADR-0149 §3).
 * The door fails soft: a mutual whose court has no room yet, or whose room is over, says
 * *You're matched* and offers nothing, which is *no door rather than a dead one*.
 */

import type { ReactNode } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { standingLine, useCourtWith, type CourtWith } from '@/features/challenges/types';
import { OPEN_THE_CHAT, useChatDoor } from '@/features/conversations/types';
import { playerName } from '@/shared/formatting/playerName';
import { Button, Tag, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import { matchedWith, saidYesTo } from '../../domain/outgoingInterest';
import type { RadarAnswer, RadarRow } from '../../domain/reading';
import { standingRelation, type StandingRelation } from '../../domain/standingRelation';
import { useMutualInterest, useOutgoingInterest } from '../../hooks/useInterest';
import {
  FOOT_ANSWER_WORDS,
  WANTS_TO_PLAY_YOU,
  YOURE_MATCHED,
  YOU_SAID_YES,
  footAnswerLabels,
} from '../radarPresentation';

export interface RadarSheetFootProps {
  readonly row: RadarRow;
  /** The reading's sport — the sport every list is read for. */
  readonly sport: Sport;
  /** One of the two answers pressed. The pane closes the sheet, withholds at the cap, and sends. */
  readonly onAnswer: (said: RadarAnswer) => void;
  /** The chat door pressed, with the room it opens. The pane closes the sheet and pushes it. */
  readonly onOpenChat: (conversationId: string) => void;
}

export function RadarSheetFoot({ row, sport, onAnswer, onOpenChat }: RadarSheetFootProps) {
  const outgoing = useOutgoingInterest().data;
  const mutual = useMutualInterest().data;
  const court = useCourtWith(row.playerId);
  const door = useChatDoor(court?.challengeId);

  const relation = standingRelation({
    ...(row.inclusionReason === undefined ? {} : { inclusionReason: row.inclusionReason }),
    saidYes: saidYesTo(outgoing, sport, row.playerId),
    matched: matchedWith(mutual, sport, row.playerId),
    court,
  });

  const labels = footAnswerLabels(playerName({ kind: 'player', name: row.card.name }));
  const notToday = (
    <Button
      label={FOOT_ANSWER_WORDS.no}
      accessibilityLabel={labels.no}
      variant="secondary"
      style={s.answer}
      onPress={() => onAnswer('no')}
    />
  );
  const letsPlay = (
    <Button
      label={FOOT_ANSWER_WORDS.yes}
      accessibilityLabel={labels.yes}
      style={s.answer}
      onPress={() => onAnswer('yes')}
    />
  );

  return (
    <View style={s.foot} testID="radar-sheet-foot">
      {footFor(relation, { notToday, letsPlay, door, onOpenChat })}
    </View>
  );
}

/** The five feet — see the module note's table. */
function footFor(
  relation: StandingRelation<CourtWith>,
  parts: {
    readonly notToday: ReactNode;
    readonly letsPlay: ReactNode;
    readonly door: string | undefined;
    readonly onOpenChat: (conversationId: string) => void;
  },
): ReactNode {
  switch (relation.kind) {
    case 'court':
      return <Text style={s.line}>{standingLine(relation.court.facts)}</Text>;
    case 'matched':
      return (
        <>
          <Text style={s.line}>{YOURE_MATCHED}</Text>
          {parts.door === undefined ? null : (
            <Button
              label={OPEN_THE_CHAT}
              variant="secondary"
              onPress={() => parts.onOpenChat(parts.door as string)}
            />
          )}
        </>
      );
    case 'said-yes':
      return (
        <View style={s.pair}>
          <View style={s.standing}>
            <Tag label={YOU_SAID_YES} />
          </View>
          {parts.notToday}
        </View>
      );
    case 'liker':
      return (
        <>
          <View style={s.tagRow}>
            <Tag label={WANTS_TO_PLAY_YOU} variant="volt" />
          </View>
          <View style={s.pair}>
            {parts.notToday}
            {parts.letsPlay}
          </View>
        </>
      );
    case 'open':
      return (
        <View style={s.pair}>
          {parts.notToday}
          {parts.letsPlay}
        </View>
      );
  }
}

const s = StyleSheet.create({
  foot: { gap: theme.space.sm },
  // The challenge screen's own pair: two controls sharing the width, the reading order the
  // swipe taught — the no on the left, the yes on the right.
  pair: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  answer: { flex: 1 },
  // The tag takes the yes's place beside *Not today*, centred in the half a button would fill.
  standing: { flex: 1, alignItems: 'center' },
  tagRow: { flexDirection: 'row' },
  // A statement of standing, in the record's own inline role: read, not operated.
  line: { ...theme.type.inlineTitle, color: theme.color.ink },
});
