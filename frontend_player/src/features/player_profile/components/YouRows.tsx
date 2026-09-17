/**
 * **This feature's rows on the You tab** — one per declared fact, each a title, a live line and
 * a door to the screen that changes it
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §1).
 *
 * The shell composes the tab — its title, the three group titles, which rows sit in which
 * group — and every row from *Skill passport* down is the feature's whose fact it is. These
 * are the profile's: the declaration, the week, the radius, the area, and the five whose
 * screens land with their contract. Each reads the fact off the read that carries it, says it
 * in one line through `youProfilePresentation`, and pushes its own screen.
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
 * | the five deferred | nothing yet — the fields land on the read with #471 and #472 |
 */

import { useRouter } from 'expo-router';

import { useSkillRatings } from '@/features/onboarding/types';
import { liveLine } from '@/shared/errors';
import { DoorRow, type DoorRowGlyph, type DoorRowProps } from '@/shared/ui';

import { playIntentRows } from '../domain/playIntentRows';
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
  DEFERRED_ROW,
  HOW_FAR_TO_LOOK_TITLE,
  WHAT_KIND_OF_GAME_TITLE,
  WHERE_YOU_PLAY_TITLE,
  YOUR_WEEK_TITLE,
  kindOfGameLine,
  radiusLine,
  weekLine,
  type DeferredRowKey,
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

const DEFERRED_ROUTE = {
  photos: YOU_PHOTOS_ROUTE,
  tags: YOU_TAGS_ROUTE,
  intro: YOU_INTRO_ROUTE,
  whoYouPlayWith: YOU_WHO_YOU_PLAY_WITH_ROUTE,
  gameSuggestions: YOU_GAME_SUGGESTIONS_ROUTE,
} as const satisfies Readonly<Record<DeferredRowKey, string>>;

const DEFERRED_GLYPH: Readonly<Record<DeferredRowKey, DoorRowGlyph>> = {
  photos: 'camera',
  tags: 'tag',
  intro: 'align-left',
  whoYouPlayWith: 'users',
  gameSuggestions: 'check-circle',
};

/**
 * One of the five rows whose screen lands with its contract — the line names what the row
 * is, and the screen behind it says so in one line.
 */
function DeferredRow({ row, divided }: YouRowProps & { readonly row: DeferredRowKey }) {
  const router = useRouter();

  return (
    <DoorRow
      glyph={DEFERRED_GLYPH[row]}
      title={DEFERRED_ROW[row].title}
      line={DEFERRED_ROW[row].line}
      divided={divided}
      onPress={() => router.push(DEFERRED_ROUTE[row])}
    />
  );
}

export const WhoYouPlayWithRow = ({ divided }: YouRowProps) => (
  <DeferredRow row="whoYouPlayWith" divided={divided} />
);
export const GameSuggestionsRow = ({ divided }: YouRowProps) => (
  <DeferredRow row="gameSuggestions" divided={divided} />
);
export const PhotosRow = ({ divided }: YouRowProps) => (
  <DeferredRow row="photos" divided={divided} />
);
export const TagsRow = ({ divided }: YouRowProps) => <DeferredRow row="tags" divided={divided} />;
export const IntroRow = ({ divided }: YouRowProps) => <DeferredRow row="intro" divided={divided} />;
