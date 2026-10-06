/**
 * Step five of onboarding's second part: **where do you play?**
 *
 * It sits after the week and before *Who you play with*, with the other answers that narrow
 * who the platform puts in front of a player. A permission prompt is the highest-friction
 * moment in the whole flow, which is why the screen explains it before asking.
 *
 * ## The explanation comes before the prompt, always
 *
 * Nothing is read on arrival, and the OS dialog cannot appear until the player presses the
 * control. What is on screen before that is the reason: what the area is used for, that it
 * is read once and rounded, and that nothing is collected while they are elsewhere. iOS
 * shows its dialog once per install, so a prompt that arrives before the sentence spends
 * the only ask this app gets.
 *
 * ## A refusal costs discovery, not the step
 *
 * Location is what search and matchmaking are worked out from — a player without an area
 * cannot find anyone and cannot be found — so this step insists, and says exactly what
 * declining costs, in the note *and* on the control that leaves. But it still leaves: being
 * stuck on step five of six behind a permission the player can change at any time is not a
 * setup flow, and the area is editable from the profile afterwards.
 *
 * ## Nothing here decides anything
 *
 * The coarsening is `locationArea`'s, the asking and the re-reading are `useLocationStep`'s,
 * and the words are `locationPresentation`'s. What is left in this file is what a player
 * sees — the same split the three steps before it made, and for the same reason: the
 * profile editor will obey these rules from a screen that looks nothing like this one.
 *
 * ## No coordinates are drawn at all
 *
 * The area used to be printed back as a degree pair. It is not any more, and the change is
 * not only cosmetic: *the precise fix never leaves the hook* was already true, and now **no
 * reading of any kind reaches the screen**. What a player gets instead is the control they
 * pressed turning green and saying `Location saved` — the fact they actually wanted, which
 * is *did that work*, rather than two numbers they cannot check and did not ask for. The
 * area still goes to the draft and the commit exactly as before.
 *
 * The green is `Button`'s `settled` variant, and the **words change with it**: a state
 * carried by a fill alone is a state nobody who cannot see the fill is told about. The one
 * moment on this step that moves — the control arriving at *settled* — is the button's own
 * (6.1, amended 2026-09-18): the coral fades into the mint under the new words, once, never on
 * the way back, and not at all under reduced motion. This step used to fade the whole control
 * for the same reason; now that every *Save* on the You tab arrives the same way, the fade
 * lives with the fill it is about.
 */

import { useRouter } from 'expo-router';
import { StyleSheet, View } from 'react-native';

import { openAppSettings } from '@/shared/lib/platform';
import { Button, Note } from '@/shared/ui';

import { stepAfter } from '../domain/socialSteps';
import { useLocationStep } from '../hooks/useLocationStep';

import { SocialStepLayout } from './SocialStepLayout';
import { SOCIAL_STEP_PATH } from './socialStepRoutes';
import { stepCopy } from './socialStepPresentation';
import {
  ACCESS_BODY,
  ACCESS_TITLE,
  NO_FIX_BODY,
  NO_FIX_TITLE,
  OPEN_SETTINGS,
  READ_AGAIN_HINT,
  READING_WORD,
  captureLabel,
  continueLabel,
  WHY_BODY,
  WHY_TITLE,
} from './locationPresentation';

export function SocialLocationStep() {
  const router = useRouter();
  const { area, standing, capture } = useLocationStep();
  const settled = area !== undefined;

  // Where continuing leads is the step order's answer, not this screen's.
  const next = stepAfter('location');
  const refusal =
    standing.access === 'refused' || standing.access === 'blocked' ? standing.access : undefined;

  return (
    <SocialStepLayout
      step="location"
      action={
        next === undefined ? null : (
          // Never disabled. The accent moves to it only once there is an area to continue
          // with — before that the ask is the important control on the screen, and the
          // label says what leaving without one costs.
          <Button
            label={continueLabel(area)}
            variant={area === undefined ? 'secondary' : 'primary'}
            size="lg"
            onPress={() => router.replace(SOCIAL_STEP_PATH[next])}
            accessibilityHint={`Goes to ${stepCopy(next).title}`}
          />
        )
      }
    >
      {/* `info` rather than `amber`: this explains what the product does with the answer,
          and amber means *watch this, reversible, not yet wrong* — a status about the
          player's own answer rather than an explanation of the app (design-system 1.3). */}
      <Note variant="info" title={WHY_TITLE}>
        {WHY_BODY}
      </Note>

      {/* The one accent, and only ever one of it (design-system 1.2): the ask is the coral
          control while there is no area, and once there is one it goes green and says so
          while the action bar's continue takes the accent. Pressing it then re-reads
          something already answered, which is why it stays a control and says which act it
          is now offering. */}
      <Button
        label={captureLabel(area)}
        variant={settled ? 'settled' : 'primary'}
        size="lg"
        busy={standing.reading}
        busyLabel={READING_WORD}
        onPress={() => void capture()}
        accessibilityHint={settled ? READ_AGAIN_HINT : 'Asks your phone for your position, once'}
      />

      {refusal === undefined ? null : (
        // Announced: a player who has just dismissed an OS dialog is looking at the
        // dialog, not at the screen underneath it.
        <Note variant="amber" accessibilityRole="alert" title={ACCESS_TITLE[refusal]}>
          {ACCESS_BODY[refusal]}
        </Note>
      )}

      {/* Only where pressing again cannot help. A settings control beside a permission the
          OS will still prompt for sends the player two screens away for one tap. */}
      {refusal === 'blocked' ? (
        <View style={s.settings}>
          <Button label={OPEN_SETTINGS} variant="secondary" onPress={openAppSettings} />
        </View>
      ) : null}

      {standing.noFix ? (
        <Note variant="amber" accessibilityRole="alert" title={NO_FIX_TITLE}>
          {NO_FIX_BODY}
        </Note>
      ) : null}
    </SocialStepLayout>
  );
}

const s = StyleSheet.create({
  settings: { alignItems: 'flex-start' },
});
