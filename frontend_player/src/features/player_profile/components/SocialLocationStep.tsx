/**
 * Step five of onboarding's second part: **where do you play?**
 *
 * It sits after the week and before *Who you play with*. A permission prompt is the
 * highest-friction moment in the whole flow, which is why the screen explains it before asking.
 *
 * ## The explanation comes before the prompt, always
 *
 * Nothing is read on arrival, and the OS dialog cannot appear until the player presses the
 * control. What is on screen before that is the reason: what the area is used for, that it
 * is rounded to about a kilometre, and that no other player is shown it. iOS
 * shows its dialog once per install, so a prompt that arrives before the sentence spends
 * the only ask this app gets.
 *
 * ## A refusal is answered with a club, and Continue waits for an area
 *
 * The area measures how far each club is and orders every club search, and a Player profile
 * cannot exist without one — so *Continue* is **drawn only once there is an area**
 * ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §10). It used to
 * be drawn always, with *Continue without matching* on it before an area, and the finish two
 * screens later then refused to go: a step that let a player past what the end would not.
 * What a refusal gets instead of a way past is **another way in**: after the phone says no —
 * denied, blocked, or no fix — the step offers *Pick a club near where you play*, and the club
 * she picks is her area. It stays drawn while a club is the answer, so walking back finds it.
 *
 * ## Nothing here decides anything
 *
 * The coarsening is `locationArea`'s, the asking, the re-reading and the pick are
 * `useLocationStep`'s, the search is `AreaClubPicker`'s over `groups`' own, and the words are
 * `locationPresentation`'s. What is left in this file is what a player sees.
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

import { AreaClubPicker } from './AreaClubPicker';
import { SocialStepLayout } from './SocialStepLayout';
import { SOCIAL_STEP_PATH } from './socialStepRoutes';
import { stepCopy } from './socialStepPresentation';
import {
  ACCESS_HOW_TO,
  ACCESS_TITLE,
  CONTINUE,
  NO_FIX_BODY,
  NO_FIX_TITLE,
  OPEN_SETTINGS,
  READ_AGAIN_HINT,
  READING_WORD,
  USE_MY_LOCATION_HINT,
  WHY_BODY,
  WHY_TITLE,
  captureLabel,
} from './locationPresentation';

export function SocialLocationStep() {
  const router = useRouter();
  const { location, standing, capture, pick, unpick } = useLocationStep();
  const fromThePhone = location?.kind === 'reading';

  // Where continuing leads is the step order's answer, not this screen's.
  const next = stepAfter('location');
  const refusal =
    standing.access === 'refused' || standing.access === 'blocked' ? standing.access : undefined;
  // The club is offered once the phone has said no, in any of its three ways — and stays while a
  // club is the answer, so the pick is on screen whenever the step is.
  const offersAClub = refusal !== undefined || standing.noFix || location?.kind === 'club';

  return (
    <SocialStepLayout
      step="location"
      action={
        // Drawn only once there is an area: a profile cannot exist without one, and a way past
        // that the finish would refuse two screens later is the contradiction ADR-0200 §10 removed.
        next === undefined || location === undefined ? null : (
          <Button
            label={CONTINUE}
            variant="primary"
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
          control while there is no area; once the phone's reading is the area it goes green and
          says so, and once a club is, it steps back to `secondary` — still the way to let the
          phone say instead — while *Continue* takes the accent. */}
      <Button
        label={captureLabel(location)}
        variant={fromThePhone ? 'settled' : location === undefined ? 'primary' : 'secondary'}
        size="lg"
        busy={standing.reading}
        busyLabel={READING_WORD}
        onPress={() => void capture()}
        accessibilityHint={fromThePhone ? READ_AGAIN_HINT : USE_MY_LOCATION_HINT}
      />

      {refusal === undefined ? null : (
        // Announced: a player who has just dismissed an OS dialog is looking at the
        // dialog, not at the screen underneath it.
        <Note variant="amber" accessibilityRole="alert" title={ACCESS_TITLE[refusal]}>
          {ACCESS_HOW_TO[refusal]}
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

      {offersAClub ? (
        <AreaClubPicker
          chosen={location?.kind === 'club' ? location.club : undefined}
          onPick={pick}
          onChange={unpick}
        />
      ) : null}
    </SocialStepLayout>
  );
}

const s = StyleSheet.create({
  settings: { alignItems: 'flex-start' },
});
