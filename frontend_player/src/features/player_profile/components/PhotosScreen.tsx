/**
 * **Photos** — the photos step as it is, under the tab's chrome, written on every change to
 * the row ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2).
 *
 * The rule note, the row, the two lines, the hold-for-options sheet and the flagged notice
 * are `CourtPhotos`, exactly as `SocialPhotosStep` draws them; the picking, the permission
 * and the uploads are `useProfilePhotos`, over a bench seeded from the profile rather than
 * the draft's (`useOwnPhotos`). The step's *Continue* is the one thing not here — and there
 * is no *Save* in its place, because the step never had one: **the row is the state**, and a
 * promotion, a removal or an upload that landed sends `PUT /players/me/photos` with the ids
 * in order. Removing the last one sends an empty list and the poster returns.
 *
 * ## Two reads before the row
 *
 * The profile read carries the ids and the verdicts; each photo's signed address is
 * `GET /photos/{id}`, read once per open (`usePhotoAddresses`). The row is drawn once every
 * address is in — a row of three assembled one tile at a time would be a row whose *first*
 * changed under the finger — and the workbench is seeded **once**, from the profile as it
 * was first read: a refetch of the profile while the player is rearranging must not put the
 * tiles back, and an upload that lands is the workbench's to know about, not the read's.
 *
 * ## A write that failed says so, once, and offers the row again
 *
 * The step has no write to fail. Here one can, and a row that quietly stopped matching the
 * profile would be the one thing a screen with no *Save* must not do: the failure is said in
 * the recovery register under the row, pinned where the step pins its ceiling refusal, with
 * *Try again* sending the row as it now stands. The next change sends it too.
 */

import { useRouter } from 'expo-router';
import { useState, type ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';

import { useCurrentUser } from '@/features/auth/types';
import { ShellScreen } from '@/features/shell/types';
import { recoveryMessage } from '@/shared/errors';
import { Button, Note, behindOverlay, theme } from '@/shared/ui';

import { heldPhotos, type ProfilePhoto, type UploadedPhoto } from '../domain/photoCollection';
import { useOwnPhotos } from '../hooks/useOwnPhotos';
import { usePhotoAddresses } from '../hooks/usePhotoAddresses';
import { useProfileSurface } from '../hooks/useProfileSurface';

import { CourtPhotos } from './CourtPhotos';
import { CEILING_BODY, CEILING_TITLE, PHOTOS_RULE } from './photoStepPresentation';
import { ProfileReadStanding } from './ProfileReadStanding';
import { stepCopy } from './socialStepPresentation';
import { LOADING_PHOTOS, TRY_AGAIN, onYourCardEyebrow } from './youProfilePresentation';

export function PhotosScreen() {
  const profile = useProfileSurface();
  const user = useCurrentUser();

  if (profile.data === undefined) {
    return (
      <PhotosChrome>
        <ProfileReadStanding
          fetchStatus={profile.fetchStatus}
          isPending={profile.isPending}
          error={profile.error}
          onRetry={() => void profile.refetch()}
          loadingLabel={LOADING_PHOTOS}
        />
      </PhotosChrome>
    );
  }

  return <PhotosFromProfile held={profile.data.photos} posterOf={user.data?.id} />;
}

/** The step's title and the rule, under the group the row was opened from. */
function PhotosChrome({
  overlaid = false,
  action,
  children,
}: {
  readonly overlaid?: boolean;
  readonly action?: ReactNode;
  readonly children: ReactNode;
}) {
  const router = useRouter();

  return (
    <View style={s.root} {...behindOverlay(overlaid)}>
      <ShellScreen
        eyebrow={onYourCardEyebrow(PHOTOS_RULE)}
        title={stepCopy('photos').title}
        onBack={router.back}
        action={action}
      >
        {children}
      </ShellScreen>
    </View>
  );
}

/**
 * The profile's photos as first read, and their addresses — then the workbench.
 *
 * `useState` with the first `held` freezes the seed: the addresses are read for those ids and
 * no others, and a profile refetched under the player does not re-seed the row.
 */
function PhotosFromProfile({
  held,
  posterOf,
}: {
  readonly held: readonly UploadedPhoto[];
  readonly posterOf: string | undefined;
}) {
  const [seed] = useState(() => held);
  const addresses = usePhotoAddresses(seed);

  if (addresses.addressOf === undefined) {
    return (
      <PhotosChrome>
        <ProfileReadStanding
          fetchStatus={addresses.isPending ? 'fetching' : 'idle'}
          isPending={addresses.isPending}
          error={addresses.error}
          onRetry={addresses.refetch}
          loadingLabel={LOADING_PHOTOS}
        />
      </PhotosChrome>
    );
  }

  return <OwnPhotos seed={heldPhotos(seed, addresses.addressOf)} posterOf={posterOf} />;
}

function OwnPhotos({
  seed,
  posterOf,
}: {
  readonly seed: readonly ProfilePhoto[];
  readonly posterOf: string | undefined;
}) {
  const workbench = useOwnPhotos(seed);

  return (
    <CourtPhotos workbench={workbench} posterOf={posterOf}>
      {(body, overlaid) => (
        <PhotosChrome
          overlaid={overlaid}
          action={
            workbench.standing.refusedAtTheCeiling || workbench.writeError !== null ? (
              <>
                {workbench.standing.refusedAtTheCeiling ? (
                  // Pinned rather than left beside the row, and announced — the step's
                  // reason: a player who picked a fourth may not be looking at the tiles.
                  <Note variant="amber" accessibilityRole="alert" title={CEILING_TITLE}>
                    {CEILING_BODY}
                  </Note>
                ) : null}

                {workbench.writeError !== null ? (
                  <View style={s.failure}>
                    <Note variant="coral" accessibilityRole="alert">
                      {recoveryMessage(workbench.writeError)}
                    </Note>
                    <Button
                      label={TRY_AGAIN}
                      variant="secondary"
                      disabled={workbench.writing}
                      onPress={workbench.retryWrite}
                    />
                  </View>
                ) : null}
              </>
            ) : undefined
          }
        >
          {body}
        </PhotosChrome>
      )}
    </CourtPhotos>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  failure: { gap: theme.space.sm },
});
