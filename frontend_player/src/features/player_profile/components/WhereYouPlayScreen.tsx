/**
 * **Where you play** — *Your area is set*, the tab's one sentence about the area, and *Read my
 * area again* in the location step's permission states
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2).
 *
 * ## One state, because onboarding cannot finish without an area
 *
 * No map, no name, no coordinate — nothing on this platform can turn the cell into a
 * neighbourhood and the screen does not pretend to — and no *not set* branch, because every
 * profile the tab can read holds an area: the commit requires one. So the card says the area
 * is set, in mint, and under it the sentence the tab has carried since the cold-start refresh
 * — that the area moves each time the app opens, and never finer than about a kilometre.
 * `AreaUpdatesNote` moved here from the tab's foot; the row's live line is the short form.
 *
 * ## The control, in the step's three states
 *
 * *Read my area again* is the location step's press through `useReadAreaAgain`, ending in
 * `PUT /players/me/location`. A refusal draws the step's own note — the title, and how to
 * allow it — with *Use my location* under it, because that is the control the note names; a
 * permission turned off in Settings draws *Open Settings* instead, since pressing again cannot
 * help; a phone that could not place itself says so. What the step's notes also said — that
 * setting up can finish without an area — is not said here, because it is not true of anybody
 * on this screen.
 *
 * ## The write says it landed, in words
 *
 * Once the cell is put, the control turns `settled` and says *Location saved*, as the step's
 * does — the fill and the words together, never the fill alone. It stays a control: pressing
 * it again reads again.
 */

import { useRouter } from 'expo-router';
import { StyleSheet, View } from 'react-native';

import { ShellScreen, YOU_COPY } from '@/features/shell/types';
import { recoveryMessage } from '@/shared/errors';
import { openAppSettings } from '@/shared/lib/platform';
import { Button, Card, Note, Tag, theme } from '@/shared/ui';

import { useReadAreaAgain } from '../hooks/useReadAreaAgain';

import { AreaUpdatesNote } from './AreaUpdatesNote';
import {
  ACCESS_HOW_TO,
  ACCESS_TITLE,
  LOCATION_SAVED,
  NO_FIX_BODY,
  NO_FIX_TITLE,
  OPEN_SETTINGS,
  READ_AGAIN_HINT,
  READING_WORD,
  USE_MY_LOCATION,
} from './locationPresentation';
import { AREA_SET, READ_AGAIN, WHERE_YOU_PLAY_TITLE } from './youProfilePresentation';

export function WhereYouPlayScreen() {
  const router = useRouter();
  const { standing, capture, write } = useReadAreaAgain();

  const refusal =
    standing.access === 'refused' || standing.access === 'blocked' ? standing.access : undefined;
  const settled = write.isSuccess && !standing.reading;

  return (
    <ShellScreen
      eyebrow={YOU_COPY.groups.findingPlayers}
      title={WHERE_YOU_PLAY_TITLE}
      onBack={router.back}
    >
      <Card style={s.state}>
        <Tag label={AREA_SET} variant="ok" />
        <AreaUpdatesNote />
      </Card>

      {refusal === undefined ? null : (
        // Announced: a player who has just dismissed an OS dialog is looking at the dialog,
        // not at the screen underneath it.
        <Note variant="amber" accessibilityRole="alert" title={ACCESS_TITLE[refusal]}>
          {ACCESS_HOW_TO[refusal]}
        </Note>
      )}

      {standing.noFix ? (
        <Note variant="amber" accessibilityRole="alert" title={NO_FIX_TITLE}>
          {NO_FIX_BODY}
        </Note>
      ) : null}

      {write.error !== null ? (
        <Note variant="coral" accessibilityRole="alert">
          {recoveryMessage(write.error)}
        </Note>
      ) : null}

      {/* Only where pressing again cannot help. A settings control beside a permission the OS
          will still prompt for sends the player two screens away for one tap. */}
      {refusal === 'blocked' ? (
        <View style={s.control}>
          <Button label={OPEN_SETTINGS} variant="secondary" onPress={openAppSettings} />
        </View>
      ) : (
        <View style={s.control}>
          <Button
            // After a refusal the note names *Use my location*, so that is what the control
            // says; otherwise it offers the act this screen is for.
            label={settled ? LOCATION_SAVED : refusal === undefined ? READ_AGAIN : USE_MY_LOCATION}
            variant={settled ? 'settled' : 'dark'}
            size="lg"
            busy={standing.reading || write.isPending}
            busyLabel={READING_WORD}
            onPress={() => void capture()}
            accessibilityHint={READ_AGAIN_HINT}
          />
        </View>
      )}
    </ShellScreen>
  );
}

const s = StyleSheet.create({
  state: { gap: theme.space.xs },
  control: { paddingTop: theme.space.xs },
});
