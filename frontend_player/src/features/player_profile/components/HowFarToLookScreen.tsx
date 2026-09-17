/**
 * **How far to look** — the radius slider as the step draws it, a draft until *Save*
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2).
 *
 * The slider is `SearchRadiusControl`, exactly as `SocialRadiusStep` drives it: the figure, the
 * plain-word reading, the track between the served bounds, the two accessibility actions. What
 * this screen adds is the one thing the step never had and the search screen has the other
 * way round — **a *Save* button, and nothing written on release.**
 *
 * ## The radius is one number, saved two ways
 *
 * Find a game writes the radius as the first half of pressing the card; that stays. Here a
 * slider that wrote on release would save a value the player was still deciding, so the slider
 * moves a draft and the button sends it. `PUT /players/me/search-radius` re-snaps to the bounds
 * and answers with the radius as held, which is what the slider then shows — the route's
 * answer written into the cache, never the draft echoed back. The draft is dropped the moment
 * the save lands, so the slider and the row's live line are one read.
 *
 * ## Two reads before the control
 *
 * The bounds come with the tag vocabulary from `GET /player-profile/options`, and the radius
 * from `GET /players/me/profile`; the slider is drawn once both are in, because a slider with
 * no bounds has no track and a track with no value has nothing on it. Each read says its own
 * standing while it is not.
 */

import { useRouter } from 'expo-router';
import { useState } from 'react';

import { ShellScreen, YOU_COPY } from '@/features/shell/types';
import { recoveryMessage } from '@/shared/errors';
import { Button, Note } from '@/shared/ui';

import { useChangeSearchRadius, useProfileSurface } from '../hooks/useProfileSurface';
import { useProfileOptions } from '../hooks/useProfileOptions';

import { ProfileReadStanding } from './ProfileReadStanding';
import { SearchRadiusControl } from './SearchRadiusControl';
import {
  HOW_FAR_TO_LOOK_TITLE,
  LOADING_DISTANCES,
  LOADING_RADIUS,
  SAVE,
  SAVED,
  SAVING,
} from './youProfilePresentation';

export function HowFarToLookScreen() {
  const router = useRouter();
  const options = useProfileOptions();
  const profile = useProfileSurface();
  const save = useChangeSearchRadius();
  /** The radius as the player has left the slider — `undefined` while it is the profile's own. */
  const [draft, setDraft] = useState<number>();

  const bounds = options.data?.searchRadius;
  const held = profile.data?.searchRadiusKm;
  const radius = draft ?? held;
  const dirty = held !== undefined && draft !== undefined && draft !== held;

  return (
    <ShellScreen
      eyebrow={YOU_COPY.groups.findingPlayers}
      title={HOW_FAR_TO_LOOK_TITLE}
      onBack={router.back}
      action={
        radius === undefined || bounds === undefined ? undefined : (
          <>
            {save.error !== null ? (
              <Note variant="coral" accessibilityRole="alert">
                {recoveryMessage(save.error)}
              </Note>
            ) : null}
            <Button
              label={dirty ? SAVE : SAVED}
              size="lg"
              disabled={!dirty}
              busy={save.isPending}
              busyLabel={SAVING}
              onPress={() => save.mutate(radius, { onSuccess: () => setDraft(undefined) })}
            />
          </>
        )
      }
    >
      <ProfileReadStanding
        fetchStatus={options.fetchStatus}
        isPending={options.isPending}
        error={options.error}
        onRetry={() => void options.refetch()}
        loadingLabel={LOADING_DISTANCES}
      />

      {/* Once, not twice: with the options in, the profile is the only read left to wait on. */}
      {options.data === undefined ? null : (
        <ProfileReadStanding
          fetchStatus={profile.fetchStatus}
          isPending={profile.isPending}
          error={profile.error}
          onRetry={() => void profile.refetch()}
          loadingLabel={LOADING_RADIUS}
        />
      )}

      {bounds === undefined || radius === undefined ? null : (
        <SearchRadiusControl radius={radius} bounds={bounds} onChange={setDraft} />
      )}
    </ShellScreen>
  );
}
