/**
 * **Where you play** — *Your area is set*, the tab's one sentence about the area, and the two ways
 * to move it: *Use my location*, and *Pick a club near where you play*
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2; [ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §10, #733).
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
 * ## Both ways, always
 *
 * *Use my location* is the location step's press through `useChangeArea`, ending in
 * `PUT /players/me/location`. A refusal draws the step's own note — the title, and how to allow
 * it or pick a club; a permission turned off in Settings draws *Open Settings* in place of the
 * press, since pressing again cannot help; a phone that could not place itself says so. *Pick a
 * club near where you play* is the step's picker, **always drawn here**, where the step draws it
 * only after a refusal: a player on the tab already holds an area, and moving it by hand is an
 * ordinary thing to want. A pick is written at once — the same route, carrying the club.
 *
 * ## The screen draws the write it last sent
 *
 * Once the phone's cell is put, *Use my location* turns `settled` and says *Location saved* — the
 * fill and the words together, never the fill alone; it stays a control, and pressing it again
 * reads again. A pick draws the club, chosen, with *Change* saying *Saving…* while the write is on
 * its way and the settled ground once it has landed. The two answer each other: a reading sent
 * after a pick takes the club off the screen as it takes it off the server, and a pick sent after
 * a reading takes the *Location saved* away. A refused write says why in coral — a club the server
 * no longer knows in its own sentence — and lets go of the club. What each state is, is
 * `useChangeArea`'s; this file draws it.
 */

import { useRouter } from 'expo-router';
import { StyleSheet, View } from 'react-native';

import { ShellScreen, YOU_COPY } from '@/features/shell/types';
import { codeMessage } from '@/shared/errors';
import { openAppSettings } from '@/shared/lib/platform';
import { Button, Card, Note, Tag, theme } from '@/shared/ui';

import { useChangeArea } from '../hooks/useChangeArea';

import { AreaClubPicker } from './AreaClubPicker';
import { AreaUpdatesNote } from './AreaUpdatesNote';
import {
  ACCESS_HOW_TO,
  ACCESS_TITLE,
  AREA_WRITE_REFUSAL,
  LOCATION_SAVED,
  NO_FIX_BODY,
  NO_FIX_TITLE,
  OPEN_SETTINGS,
  READ_AGAIN_HINT,
  READING_WORD,
  USE_MY_LOCATION,
  USE_MY_LOCATION_HINT,
} from './locationPresentation';
import { AREA_SET, WHERE_YOU_PLAY_TITLE } from './youProfilePresentation';

export function WhereYouPlayScreen() {
  const router = useRouter();
  const area = useChangeArea();
  const { standing } = area;

  const refusal =
    standing.access === 'refused' || standing.access === 'blocked' ? standing.access : undefined;

  return (
    <ShellScreen
      eyebrow={YOU_COPY.groups.yourGames}
      title={WHERE_YOU_PLAY_TITLE}
      onBack={router.back}
      // The picker types, and a tap on a club while the keyboard is up should pick it.
      avoidsKeyboard
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

      {area.error !== null ? (
        <Note variant="coral" accessibilityRole="alert">
          {codeMessage(AREA_WRITE_REFUSAL, area.error)}
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
            label={area.readingSaved ? LOCATION_SAVED : USE_MY_LOCATION}
            variant={area.readingSaved ? 'settled' : 'dark'}
            size="lg"
            busy={area.readingOnItsWay}
            busyLabel={READING_WORD}
            onPress={() => void area.capture()}
            accessibilityHint={area.readingSaved ? READ_AGAIN_HINT : USE_MY_LOCATION_HINT}
          />
        </View>
      )}

      <AreaClubPicker
        chosen={area.chosenClub}
        onPick={area.pick}
        onChange={area.letGoOfClub}
        saving={area.savingClub}
      />
    </ShellScreen>
  );
}

const s = StyleSheet.create({
  state: { gap: theme.space.xs },
  control: { paddingTop: theme.space.xs },
});
