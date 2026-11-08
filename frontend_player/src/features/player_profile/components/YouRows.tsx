/**
 * **This feature's rows on the You tab** — one per declared fact, each a title, a live line and
 * a door to the screen that changes it
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §1).
 *
 * The shell composes the tab — its title, the three group titles, which rows sit in which
 * group — and every row from *Skill passport* down is the feature's whose fact it is. These
 * are the profile's: the declaration, the week, the area, who the player is matched with, the
 * photos, the tags and the intro. Each reads the fact off the read that carries it, says it in
 * one line through `youProfilePresentation`, and pushes its own screen.
 *
 * ## A live line is a read, and a read has three states
 *
 * `liveLine` draws the fact once it is in, nothing while it is on its way, and the recovery
 * sentence where it failed. Nothing is copied anywhere: the week under *Your week* is the
 * profile surface's `week`, and a save on the screen behind it writes the route's answer into
 * that cache, which is what makes the line follow.
 *
 * ## Which read each row is drawn from
 *
 * | Row | Read |
 * | --- | --- |
 * | What kind of game | `GET /ratings` ∩ `GET /players/me/profile`.play_intents |
 * | Your week | `GET /players/me/profile`.weekly_hours |
 * | Where you play | nothing — the one state, because a profile cannot be committed without an area |
 * | Who you play with | `GET /players/me/profile`.gender_preference — **the preference only**, never the gender (ADR-0179 §4) |
 * | Photos | `GET /players/me/profile`.photos — the count, and the profile photo's verdict |
 * | Tags | `GET /players/me/profile`.social_tags ∩ `GET /player-profile/options`.social_tag_selection — the ceiling is served |
 * | Intro | `GET /players/me/profile`.intro |
 * | Show me in General | `GET /players/me/profile`.ranking_visibility — **the row is the switch** |
 *
 * ## The one row that is not a door
 *
 * *Show me in General* (#778; the You spec §3.14) opens nothing: the row is the design system's
 * switch, in the door rows' lead and type so it lines up under them, and it **writes at once**, with
 * no *Save*. A refused write puts it back and says why, in a coral note under the row. It is drawn
 * once the profile read has landed, and not at all while it has not — there is no switch to draw on
 * a guess, and a mode with nothing to switch is a row that is not on screen (6.12); the rows above it
 * already say a failed read's recovery sentence.
 */

import { useRouter } from 'expo-router';
import { StyleSheet, View } from 'react-native';

import { useSkillRatings } from '@/features/onboarding/types';
import { liveLine, recoveryMessage } from '@/shared/errors';
import { DoorRow, Note, Switch, theme, type DoorRowProps } from '@/shared/ui';

import { playIntentRows } from '../domain/playIntentRows';
import { useProfileOptions } from '../hooks/useProfileOptions';
import { useProfileSurface } from '../hooks/useProfileSurface';
import { useShowMeInGeneral } from '../hooks/useShowMeInGeneral';

import {
  YOU_AREA_ROUTE,
  YOU_INTRO_ROUTE,
  YOU_KIND_OF_GAME_ROUTE,
  YOU_PHOTOS_ROUTE,
  YOU_TAGS_ROUTE,
  YOU_WEEK_ROUTE,
  YOU_WHO_YOU_PLAY_WITH_ROUTE,
} from './youProfileRoutes';
import {
  AREA_LINE,
  INTRO_TITLE,
  PHOTOS_TITLE,
  SHOW_ME_IN_GENERAL_LINE,
  SHOW_ME_IN_GENERAL_TITLE,
  TAGS_TITLE,
  WHAT_KIND_OF_GAME_TITLE,
  WHERE_YOU_PLAY_TITLE,
  WHO_YOU_PLAY_WITH_TITLE,
  YOUR_WEEK_TITLE,
  introLine,
  kindOfGameLine,
  photosLine,
  tagsLine,
  weekLine,
  whoYouPlayWithLine,
} from './youProfilePresentation';

/** 5.5's `index > 0` — the shell says where in its card the row sits. */
export type YouRowProps = Pick<DoorRowProps, 'divided'>;

export function WhatKindOfGameRow({ divided }: YouRowProps) {
  const router = useRouter();
  const ratings = useSkillRatings();
  const profile = useProfileSurface();

  // Two reads, and the line waits for both: an empty declaration map standing in for the
  // second would say *not set* about every sport for the length of a round trip.
  const both =
    ratings.data === undefined || profile.data === undefined
      ? undefined
      : playIntentRows(
          ratings.data.map((rating) => rating.sport),
          profile.data.playIntents,
        );

  return (
    <DoorRow
      glyph="play"
      title={WHAT_KIND_OF_GAME_TITLE}
      line={liveLine({ data: both, error: ratings.error ?? profile.error }, kindOfGameLine)}
      divided={divided}
      onPress={() => router.push(YOU_KIND_OF_GAME_ROUTE)}
    />
  );
}

export function YourWeekRow({ divided }: YouRowProps) {
  const router = useRouter();
  const profile = useProfileSurface();

  return (
    <DoorRow
      glyph="calendar"
      title={YOUR_WEEK_TITLE}
      line={liveLine(profile, (surface) => weekLine(surface.week))}
      divided={divided}
      onPress={() => router.push(YOU_WEEK_ROUTE)}
    />
  );
}

export function WhereYouPlayRow({ divided }: YouRowProps) {
  const router = useRouter();

  return (
    <DoorRow
      glyph="map-pin"
      title={WHERE_YOU_PLAY_TITLE}
      line={AREA_LINE}
      divided={divided}
      onPress={() => router.push(YOU_AREA_ROUTE)}
    />
  );
}

export function WhoYouPlayWithRow({ divided }: YouRowProps) {
  const router = useRouter();
  const profile = useProfileSurface();

  return (
    <DoorRow
      glyph="users"
      title={WHO_YOU_PLAY_WITH_TITLE}
      // The preference and only the preference: the gender is on the read for the screen
      // behind this row to pre-select from, and the row is not that screen.
      line={liveLine(profile, (surface) => whoYouPlayWithLine(surface.genderPreference))}
      divided={divided}
      onPress={() => router.push(YOU_WHO_YOU_PLAY_WITH_ROUTE)}
    />
  );
}

export function PhotosRow({ divided }: YouRowProps) {
  const router = useRouter();
  const profile = useProfileSurface();

  return (
    <DoorRow
      glyph="camera"
      title={PHOTOS_TITLE}
      line={liveLine(profile, (surface) => photosLine(surface.photos))}
      divided={divided}
      onPress={() => router.push(YOU_PHOTOS_ROUTE)}
    />
  );
}

export function TagsRow({ divided }: YouRowProps) {
  const router = useRouter();
  const profile = useProfileSurface();
  const options = useProfileOptions();

  // Two reads, and the line waits for both: the ceiling it counts against is served, and
  // *4 of ?* is not a sentence.
  const both =
    profile.data === undefined || options.data === undefined
      ? undefined
      : { tagIds: profile.data.socialTagIds, maximum: options.data.socialTagSelection.maximum };

  return (
    <DoorRow
      glyph="tag"
      title={TAGS_TITLE}
      line={liveLine({ data: both, error: profile.error ?? options.error }, (read) =>
        tagsLine(read.tagIds, read.maximum),
      )}
      divided={divided}
      onPress={() => router.push(YOU_TAGS_ROUTE)}
    />
  );
}

export function IntroRow({ divided }: YouRowProps) {
  const router = useRouter();
  const profile = useProfileSurface();

  return (
    <DoorRow
      glyph="align-left"
      title={INTRO_TITLE}
      line={liveLine(profile, (surface) => introLine(surface.intro))}
      divided={divided}
      onPress={() => router.push(YOU_INTRO_ROUTE)}
    />
  );
}

export function ShowMeInGeneralRow({ divided }: YouRowProps) {
  const showMe = useShowMeInGeneral();
  if (showMe.checked === undefined) return null;

  return (
    <View>
      <Switch
        door={{ glyph: 'eye', divided: divided ?? false }}
        label={SHOW_ME_IN_GENERAL_TITLE}
        description={SHOW_ME_IN_GENERAL_LINE}
        checked={showMe.checked}
        onChange={showMe.change}
      />
      {showMe.writeError === null ? null : (
        <View style={s.refused}>
          <Note variant="coral" accessibilityRole="alert">
            {recoveryMessage(showMe.writeError)}
          </Note>
        </View>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  // Under the row and inside the card, off the row's foot by the card's own small step.
  refused: { marginBottom: theme.space.sm },
});
