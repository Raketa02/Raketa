/**
 * **Intro** — the intro step's box under the tab's chrome, a draft until *Save*, and
 * *Remove intro* beside it
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2, §6 — the day [ADR-0170](../../../../../docs/adr/0170-a-player-may-write-one-line-and-it-is-read-as-their-own.md)
 * §5 named, when the intro becomes editable with the tags and the photos as one piece of work).
 *
 * The box, the counter, the hint and the rule are `IntroField`, exactly as `SocialIntroStep`
 * draws them. What this screen adds is the two controls the step never had: *Save*, sending
 * `PUT /players/me/intro` with the trimmed line, and *Remove intro*, sending the same route
 * with no line — offered only while the profile holds one, because withdrawing nothing is
 * not an act.
 *
 * ## The three refusals, and where each lands
 *
 * The two shape refusals — *too long*, *multiline* — are read off the draft by `introStanding`
 * and shut *Save* before anything is sent, drawn under the box in the step's own sentences.
 * The third, `contains_contact`, is the server's pattern and never this app's: it lands on the
 * reply, and is drawn **in the same place from the same table** (`introRefusalSentence`), so a
 * player reads one kind of sentence about their line whichever side refused it. On the step
 * that refusal was six screens away; here it is one press away, which is what the rule under
 * the box was written for. A refusal is cleared by the next keystroke, because the line it was
 * about is gone.
 *
 * ## A draft until the button, and blank is not a save
 *
 * The box opens on the line the profile holds and every keystroke moves a draft; *Save* is
 * shut while the draft is the line held, trimmed, and shut on a blank box — the way to no
 * intro is *Remove intro*, said with the control that says so, never a save of nothing. On a
 * save the cache holds the line sent (the use case says why that is the line held) and the
 * draft is dropped; on a removal the cache holds none, the box empties, and the control goes.
 */

import { useRouter } from 'expo-router';
import { useState } from 'react';

import { ShellScreen } from '@/features/shell/types';
import { recoveryMessage } from '@/shared/errors';
import { Button, Note } from '@/shared/ui';

import { introRefusal, introStanding } from '../domain/intro';
import { useChangeIntro, useProfileSurface } from '../hooks/useProfileSurface';

import { IntroField } from './IntroField';
import { INTRO_REFUSAL_SENTENCE, introRefusalSentence } from './introPresentation';
import { ProfileReadStanding } from './ProfileReadStanding';
import {
  INTRO_TITLE,
  LOADING_INTRO,
  REMOVE_INTRO,
  REMOVING,
  SAVE,
  SAVED,
  SAVING,
  onYourCardEyebrow,
} from './youProfilePresentation';

export function IntroScreen() {
  const router = useRouter();
  const profile = useProfileSurface();
  const save = useChangeIntro();
  /** The box as the player has left it — `undefined` while it shows the profile's own line. */
  const [draft, setDraft] = useState<string>();

  const held = profile.data === undefined ? undefined : profile.data.intro;
  const written = draft ?? held ?? '';
  const standing = introStanding(written);
  // Trimmed against trimmed: the line the profile holds is already the server's trim.
  const line = standing.kind === 'written' ? standing.line : undefined;
  const dirty = draft !== undefined && line !== held;

  // The refusal under the box: the shape the screen pre-empts, or the reason the server
  // answered with — one table for both.
  const refusedByServer = save.error === null ? undefined : introRefusal(save.error);
  const refusal =
    standing.kind === 'refused'
      ? INTRO_REFUSAL_SENTENCE[standing.reason]
      : refusedByServer === undefined
        ? undefined
        : introRefusalSentence(refusedByServer.reason);
  // A failure that is not the intro's — the connection, a session — is said in the recovery
  // register under the controls, where every other save on the tab says it.
  const otherFailure = save.error !== null && refusedByServer === undefined ? save.error : null;

  const change = (text: string) => {
    // The refusal was about the line that is gone. `reset` lands on the next tick, which is
    // soon enough: the next render already draws the new line.
    if (save.error !== null) save.reset();
    setDraft(text);
  };

  /** What the busy button says — the act it is in the middle of, never both. */
  const [act, setAct] = useState<'save' | 'remove'>('save');

  return (
    <ShellScreen
      eyebrow={onYourCardEyebrow()}
      title={INTRO_TITLE}
      onBack={router.back}
      avoidsKeyboard
      action={
        profile.data === undefined ? undefined : (
          <>
            {otherFailure !== null ? (
              <Note variant="coral" accessibilityRole="alert">
                {recoveryMessage(otherFailure)}
              </Note>
            ) : null}

            <Button
              label={dirty ? SAVE : SAVED}
              size="lg"
              // Shut on a line the server would refuse on shape, on a blank box — the way to
              // none is the control below — and on the line already held.
              disabled={!dirty || line === undefined}
              busy={save.isPending && act === 'save'}
              busyLabel={SAVING}
              // A blocked control names what is wrong rather than merely being grey.
              {...(refusal === undefined ? {} : { accessibilityHint: refusal })}
              onPress={() => {
                setAct('save');
                save.mutate(line, { onSuccess: () => setDraft(undefined) });
              }}
            />

            {held === undefined ? null : (
              <Button
                label={REMOVE_INTRO}
                variant="secondary"
                size="lg"
                disabled={save.isPending}
                busy={save.isPending && act === 'remove'}
                busyLabel={REMOVING}
                onPress={() => {
                  setAct('remove');
                  save.mutate(undefined, { onSuccess: () => setDraft(undefined) });
                }}
              />
            )}
          </>
        )
      }
    >
      <ProfileReadStanding
        fetchStatus={profile.fetchStatus}
        isPending={profile.isPending}
        error={profile.error}
        onRetry={() => void profile.refetch()}
        loadingLabel={LOADING_INTRO}
      />

      {profile.data === undefined ? null : (
        <IntroField written={written} onChangeText={change} refusal={refusal} />
      )}
    </ShellScreen>
  );
}
