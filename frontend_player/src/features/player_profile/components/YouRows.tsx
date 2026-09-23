/**
 * **This feature's rows on the You tab** — one per declared fact, each a title, a live line and
 * a door to the screen that changes it
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §1).
 *
 * The shell composes the tab — its title, the three group titles, which rows sit in which
 * group — and every row from *Skill passport* down is the feature's whose fact it is. These
 * are the profile's: the declaration, the week, the radius, the area, who the player is
 * matched with, the standing answer to the proposals question, the photos, the tags and the
 * intro. Each reads the fact off the read that carries it, says it in one line through
 * `youProfilePresentation`, and pushes its own screen.
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
 * | Your week | `GET /players/me/profile`.availability |
 * | How far to look | `GET /players/me/profile`.search_radius_km |
 * | Where you play | nothing — the one state, because a profile cannot be committed without an area |
 * | Who you play with | `GET /players/me/profile`.gender_preference — **the preference only**, never the gender (ADR-0179 §4) |
 * | Game suggestions | `GET /players/me/profile`.proposals_opt_in — the answer and its day |
 * | Photos | `GET /players/me/profile`.photos — the count, and the profile photo's verdict |
 * | Tags | `GET /players/me/profile`.social_tags ∩ `GET /player-profile/options`.social_tag_selection — the ceiling is served |
 * | Intro | `GET /players/me/profile`.intro |
 */

import { useRouter } from 'expo-router';

import { useSkillRatings } from '@/features/onboarding/types';
import { liveLine } from '@/shared/errors';
import { DoorRow, type DoorRowProps } from '@/shared/ui';

import { playIntentRows } from '../domain/playIntentRows';
import { useProfileOptions } from '../hooks/useProfileOptions';
import { useProfileSurface } from '../hooks/useProfileSurface';

import {
  YOU_AREA_ROUTE,
  YOU_GAME_SUGGESTIONS_ROUTE,
  YOU_INTRO_ROUTE,
  YOU_KIND_OF_GAME_ROUTE,
  YOU_PHOTOS_ROUTE,
  YOU_RADIUS_ROUTE,
  YOU_TAGS_ROUTE,
  YOU_WEEK_ROUTE,
  YOU_WHO_YOU_PLAY_WITH_ROUTE,
} from './youProfileRoutes';
import {
  AREA_LINE,
  GAME_SUGGESTIONS_TITLE,
  HOW_FAR_TO_LOOK_TITLE,
  INTRO_TITLE,
  PHOTOS_TITLE,
  TAGS_TITLE,
  WHAT_KIND_OF_GAME_TITLE,
  WHERE_YOU_PLAY_TITLE,
  WHO_YOU_PLAY_WITH_TITLE,
  YOUR_WEEK_TITLE,
  gameSuggestionsLine,
  introLine,
  kindOfGameLine,
  photosLine,
  radiusLine,
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

export function HowFarToLookRow({ divided }: YouRowProps) {
  const router = useRouter();
  const profile = useProfileSurface();

  return (
    <DoorRow
      glyph="target"
      title={HOW_FAR_TO_LOOK_TITLE}
      line={liveLine(profile, (surface) => radiusLine(surface.searchRadiusKm))}
      divided={divided}
      onPress={() => router.push(YOU_RADIUS_ROUTE)}
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

export function GameSuggestionsRow({ divided }: YouRowProps) {
  const router = useRouter();
  const profile = useProfileSurface();

  return (
    <DoorRow
      glyph="check-circle"
      title={GAME_SUGGESTIONS_TITLE}
      line={liveLine(profile, (surface) => gameSuggestionsLine(surface.proposalsOptIn))}
      divided={divided}
      onPress={() => router.push(YOU_GAME_SUGGESTIONS_ROUTE)}
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
