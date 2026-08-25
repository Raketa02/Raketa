/**
 * Step four of onboarding's second part: **where do you play?**
 *
 * It sits immediately before the radius on purpose. A permission prompt is the
 * highest-friction moment in the whole flow, and asking it here means the *next* screen —
 * how far out do you want to look — visibly explains what it was for.
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
 * stuck on step four of six behind a permission the player can change at any time is not a
 * setup flow, and the area is editable from the profile afterwards.
 *
 * ## Nothing here decides anything
 *
 * The coarsening is `locationArea`'s, the asking and the re-reading are `useLocationStep`'s,
 * and the words are `locationPresentation`'s. What is left in this file is what a player
 * sees — the same split the three steps before it made, and for the same reason: the
 * profile editor will obey these rules from a screen that looks nothing like this one.
 *
 * **Only the coarse area is ever drawn.** The figure on screen is the same pair the draft
 * holds and the same pair the commit will send; there is no precise reading anywhere above
 * the hook that could be rendered by accident.
 */

import { useRouter } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { openAppSettings } from '@/shared/lib/platform';
import { Button, Card, Note, Row, theme } from '@/shared/ui';

import { stepAfter } from '../domain/socialSteps';
import { useLocationStep } from '../hooks/useLocationStep';

import { SocialStepLayout } from './SocialStepLayout';
import { SOCIAL_STEP_PATH } from './socialStepRoutes';
import { stepCopy } from './socialStepPresentation';
import {
  ACCESS_BODY,
  ACCESS_TITLE,
  AREA_LABEL,
  AREA_PRECISION_LINE,
  AREA_UNSET_LINE,
  NO_FIX_BODY,
  NO_FIX_TITLE,
  OPEN_SETTINGS,
  READING_WORD,
  USE_MY_LOCATION,
  WHY_BODY,
  WHY_TITLE,
  areaLine,
  continueLabel,
  spokenArea,
} from './locationPresentation';

export function SocialLocationStep() {
  const router = useRouter();
  const { area, standing, capture } = useLocationStep();

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
      <Text style={s.note}>{stepCopy('location').asks}</Text>

      {/* `info` rather than `amber`: this explains what the product does with the answer,
          and amber means *watch this, reversible, not yet wrong* — a status about the
          player's own answer rather than an explanation of the app (design-system 1.3). */}
      <Note variant="info" title={WHY_TITLE}>
        {WHY_BODY}
      </Note>

      {/* The one accent, and only ever one of it (design-system 1.2): the ask is the coral
          control while there is no area, and the action bar's continue takes it once there
          is — at which point pressing this again only re-reads something already answered. */}
      <Button
        label={USE_MY_LOCATION}
        variant={area === undefined ? 'primary' : 'secondary'}
        size="lg"
        busy={standing.reading}
        busyLabel={READING_WORD}
        onPress={() => void capture()}
        accessibilityHint="Asks your phone for your position, once"
      />

      {area !== undefined ? (
        <Card style={s.area}>
          {/* One accessibility element: a coordinate pair read a screen apart from the
              words that name it is two halves of a fact (design-system 5.5). */}
          <Row
            label={AREA_LABEL}
            value={<Text style={s.figure}>{areaLine(area)}</Text>}
            accessibilityLabel={spokenArea(area)}
          />
          <Text style={s.note}>{AREA_PRECISION_LINE}</Text>
        </Card>
      ) : standing.access === 'unasked' ? (
        // Said only while it is true. A phone that has already been asked and answered has
        // read something, whether or not it could place itself.
        <Text style={s.note}>{AREA_UNSET_LINE}</Text>
      ) : null}

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
  /** Secondary text is always `tiny` in `muted` — what this step asks, and its two lines. */
  note: { ...theme.type.tiny, color: theme.color.muted },
  area: { gap: theme.space.xxs },
  /** A figure, so mono and tabular: design-system 1.4 admits no exception. */
  figure: { ...theme.num.xs, ...theme.tabular, color: theme.color.ink },
  settings: { alignItems: 'flex-start' },
});
