/**
 * **Game suggestions** — the opt-in step's promises under the tab's chrome, the standing
 * answer with its evidence, and the two answers, **each of which writes on every press**
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2, §8).
 *
 * The card is `OptInPromises` with the profile's three — the third says *from here*, because
 * here is where the player is standing — under the step's scope line, which is the one
 * sentence that makes *no* a decision about proposals rather than about being seen at all.
 * What the step said about its own controls is not said here: *never pre-ticked* is a claim
 * about a question not yet answered, and this screen opens on the answer already given.
 *
 * ## The answer is a record, and the card draws the record
 *
 * *Your answer* — `Yes` or `No` as a tag — and under it when, against which words and from
 * which screen: **the evidence** (`CONTEXT.md` — *Consent is evidenced, not asserted*), read
 * off `GET /players/me/profile` and never composed here. Pressing either answer, the standing
 * one included, sends `PUT /players/me/proposals-opt-in` with the version on this screen, and
 * **the card follows the reply**: the route answers with the record it made — the server's
 * clock, the route's surface — and that is what the cache holds, never the press. There is no
 * *Save* and no draft, because there is nothing to hold back: a press is the answer, and the
 * question is asked again by asking it.
 *
 * A refused press changes nothing on the card — the standing answer is still the standing
 * answer — and says why under the controls; the control that failed is the retry.
 */

import { useRouter } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { ShellScreen, YOU_COPY } from '@/features/shell/types';
import { recoveryMessage } from '@/shared/errors';
import { Button, Card, Note, Row, Tag, theme } from '@/shared/ui';

import { useAnswerProposalsOptIn, useProfileSurface } from '../hooks/useProfileSurface';

import { OptInPromises } from './OptInPromises';
import {
  OPT_IN_ANSWERS,
  OPT_IN_PROMISES_ON_PROFILE,
  OPT_IN_SCOPE,
  PROPOSALS_OPT_IN_COPY_VERSION,
} from './optInPresentation';
import { ProfileReadStanding } from './ProfileReadStanding';
import {
  GAME_SUGGESTIONS_TITLE,
  LOADING_GAME_SUGGESTIONS,
  YOUR_ANSWER,
  answerGivenLine,
  answerWord,
} from './youProfilePresentation';

export function GameSuggestionsScreen() {
  const router = useRouter();
  const profile = useProfileSurface();
  const record = useAnswerProposalsOptIn();

  /**
   * Record the answer **with the words it was given against**, always together — the step's
   * rule, from the screen that drew these sentences. Every press writes, the standing answer
   * included: re-affirming an answer is itself a fact about consent.
   */
  const answerAgain = (accepted: boolean) =>
    record.mutate({ accepted, copyVersion: PROPOSALS_OPT_IN_COPY_VERSION });

  const answer = profile.data?.proposalsOptIn;
  /** Which of the two is on its way — the mutation's own record of what it was sent. */
  const inFlight = record.isPending ? record.variables.accepted : undefined;

  return (
    <ShellScreen
      eyebrow={YOU_COPY.groups.findingPlayers}
      title={GAME_SUGGESTIONS_TITLE}
      onBack={router.back}
    >
      <ProfileReadStanding
        fetchStatus={profile.fetchStatus}
        isPending={profile.isPending}
        error={profile.error}
        onRetry={() => void profile.refetch()}
        loadingLabel={LOADING_GAME_SUGGESTIONS}
      />

      {answer === undefined ? null : (
        <>
          {/* First, above the card, for the step's reason: the promises are conditional on a
              yes, and the reader who most needs this sentence is the one not giving it. */}
          <Note variant="info">{OPT_IN_SCOPE}</Note>

          <OptInPromises promises={OPT_IN_PROMISES_ON_PROFILE} />

          <Card style={s.answer}>
            {/* One element to a listener: the label and the word mean nothing a screen apart.
                `ok` for a yes — settled, mint — and `base` for a no, which is a complete answer
                and not a warning about anything. */}
            <Row
              label={YOUR_ANSWER}
              value={
                <Tag
                  label={answerWord(answer.accepted)}
                  variant={answer.accepted ? 'ok' : 'base'}
                />
              }
              accessibilityLabel={`${YOUR_ANSWER}: ${answerWord(answer.accepted)}`}
            />
            <Text style={s.evidence}>{answerGivenLine(answer)}</Text>

            {record.error !== null ? (
              <Note variant="coral" accessibilityRole="alert">
                {recoveryMessage(record.error)}
              </Note>
            ) : null}

            {/* The order is the copy's, not this screen's — No first, because the option a
                screen puts first is the one it reads as recommending. The given one is `dark`
                and the other `secondary`, and `selected` says the same fact to whoever sees
                neither. The pressed one is busy under its own label — the press is the answer,
                and there is no other word for what it is doing — and the other waits. */}
            <View style={s.answers}>
              {OPT_IN_ANSWERS.map(({ accepted, label }) => {
                const chosen = answer.accepted === accepted;

                return (
                  <Button
                    key={label}
                    label={label}
                    size="lg"
                    variant={chosen ? 'dark' : 'secondary'}
                    selected={chosen}
                    disabled={inFlight !== undefined && inFlight !== accepted}
                    busy={inFlight === accepted}
                    onPress={() => answerAgain(accepted)}
                  />
                );
              })}
            </View>
          </Card>
        </>
      )}
    </ShellScreen>
  );
}

const s = StyleSheet.create({
  answer: { gap: theme.space.sm },
  evidence: { ...theme.type.tiny, color: theme.color.muted },
  // Stacked, not a row: both labels are a sentence naming what they do, and two of those
  // side by side on a phone are two clipped words.
  answers: { gap: theme.space.sm },
});
