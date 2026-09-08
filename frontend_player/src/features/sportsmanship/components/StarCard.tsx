/**
 * **One court, everybody who was on it, and one press that closes the question for ever.**
 *
 * In doubles that is three people — both opponents *and* your partner, because the person who
 * saw you play closest was on your own side of the net — and in singles the one opponent.
 * There is no *side* anywhere on this card and there must not be: you rate everybody else on
 * the court and nobody else.
 *
 * ## Everything a player cannot take back is said before the press
 *
 * The contract's own instruction is *"there is no correction path — so ask before you send"*,
 * and this card asks by **stating**: what a star does (`matchingLine`, above the rows rather
 * than beside the button, because a player decides what a star means while they are tapping),
 * that anybody may be left blank, and that sending closes the card. A pre-send sheet was
 * weighed and refused — see `starsPresentation.ts` — and what stands in its place is a control
 * that can be pressed a second time to clear a slip.
 *
 * ## The draft lives exactly as long as the card
 *
 * `useState` and nothing else. There is no store, no route param and nothing persisted: a card
 * is answered once, in one sitting, and a draft that outlived the list it was typed on would
 * be an opinion about an evening the player is no longer looking at. It is keyed by the game
 * in the list above, so a refetch that returns the same card returns to the same half-filled
 * one.
 *
 * ## Neither the read nor the write is optimistic, and the card does not disappear on a tap
 *
 * It goes when the list says it has gone. **Submitting closes the card for ever**, so an
 * optimistic removal that had to be rolled back would put a question the player believes they
 * answered back in front of them — and the whole cost of doing it honestly is one refetch of a
 * list that is usually empty.
 */

import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { sportLabel } from '@/features/onboarding/types';
import { playerName } from '@/shared/formatting/playerName';
import { offlineMessage } from '@/shared/errors';
import { Button, Card, Hairline, Note, StarRow, theme } from '@/shared/ui';

import type { CardOnACourt } from '../domain/card';
import { NOTHING_SAID, pressed, starsFor, type StarsDraft } from '../domain/stars';
import { useAnswerCard } from '../hooks/useCards';

import {
  CLEAR_HINT,
  LEAVE_ANYBODY_BLANK,
  SENDING_LABEL,
  matchingLine,
  starNames,
  starsErrorMessage,
  submitLabel,
  submitName,
} from './starsPresentation';

export function StarCard({ card, court, subjects }: CardOnACourt) {
  const [draft, setDraft] = useState<StarsDraft>(NOTHING_SAID);
  const answer = useAnswerCard();

  const sportName = sportLabel(court.sport);
  // Counted off the people this card **draws**, which is the one list it holds: `subjects` is
  // `card.players` named, and what the answer is assembled against is the card, in the
  // use-case. Two traversals of one list rather than two lists.
  const given = subjects.filter((one) => starsFor(draft, one.playerId) !== undefined).length;
  const label = submitLabel(given);

  // A paused mutation is not in flight at all — `networkMode: 'online'` holds it until the
  // connection returns — so the button is not busy and the sentence beside it is what says why.
  const sending = answer.isPending && !answer.isPaused;
  /**
   * **The control closes rather than merely stopping being busy**, which is the builder's own
   * shape for a write with no connection to make it over.
   *
   * There is no `Idempotency-Key` here and there must not be — one answer per card is a rule
   * that does not expire and a key does — so **the closed button is the whole of what stands
   * between a paused send and a second one**. A pressable button over a queued mutation would
   * queue a second, and on reconnect the first would close the card and the second would come
   * back `you_have_already_rated_this_game`: the player whose answer landed would read that
   * they had already answered. It stays closed after a success for the same window's sake —
   * the card is going, and until the list says so there is nothing left to press.
   */
  const closed = answer.isPaused || answer.isSuccess;

  return (
    <Card>
      <Text style={s.eyebrow}>{sportName}</Text>
      <Text style={s.gloss}>{matchingLine(subjects)}</Text>

      <View style={s.people}>
        {subjects.map((subject) => (
          <View key={subject.playerId} style={s.person}>
            {/* The whole handle, never a stem: this is a sentence's register rather than a
                seat caption's, and ADR-0107 §4 forbids deriving a familiar form from one. */}
            <Text style={s.handle}>{playerName(subject.name)}</Text>
            <StarRow
              stars={starsFor(draft, subject.playerId)}
              names={starNames(subject)}
              clearHint={CLEAR_HINT}
              onPress={(value) =>
                setDraft((standing) => pressed(standing, subject.playerId, value))
              }
              disabled={sending || closed}
            />
          </View>
        ))}
      </View>

      <Hairline style={s.foot}>
        <Text style={s.gloss}>{LEAVE_ANYBODY_BLANK}</Text>

        {/* Part 11: the sentence sits **beside the act that is waiting**. A paused mutation is
            not in flight, so a busy button would be the one thing that is not true about it. */}
        {answer.isPaused ? <Note variant="amber">{offlineMessage('resumes')}</Note> : null}
        {answer.error === null ? null : (
          <Note variant="coral" accessibilityRole="alert">
            {starsErrorMessage(answer.error)}
          </Note>
        )}

        <Button
          label={label}
          accessibilityLabel={submitName(label, sportName, subjects)}
          onPress={() => answer.mutate({ card, draft })}
          busy={sending}
          busyLabel={SENDING_LABEL}
          disabled={closed}
        />
      </Hairline>
    </Card>
  );
}

const s = StyleSheet.create({
  eyebrow: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: 'uppercase',
    marginBottom: theme.space.xxs,
  },
  gloss: { ...theme.type.tiny, color: theme.color.muted },
  people: { gap: theme.space.sm, paddingTop: theme.space.sm },
  foot: { gap: theme.space.sm },
  // The handle on its own line above the stars rather than beside them: five 44pt targets is
  // 220pt, and a sixty-four-character handle in what is left of a card would be clipped on
  // every phone in the population.
  person: { gap: theme.space.xxs },
  handle: { ...theme.type.rlValue, color: theme.color.ink },
});
