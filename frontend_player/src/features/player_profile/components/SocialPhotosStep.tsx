/**
 * Step three of onboarding's second part: **your court photos**.
 *
 * Up to three photos of the player on a court, or none. It is one of the two steps of the eight
 * that can be finished without answering anything — the intro before it is the other — and the
 * screen says so before a player has to work it out — a player who adds nothing gets a court
 * poster generated from their own id, which is what stops *optional* meaning *an empty box on
 * your profile*.
 *
 * ## Nothing here decides anything, and little here is drawn
 *
 * The ceiling, the order, what promotion means and which ids reach the draft are
 * `photoCollection`'s, with their own tests and no renderer. Picking, the permission and
 * the upload queue are `useProfilePhotos`', over the **draft's** bench — the workbench
 * beside the part's draft, whose every change writes the ids it yields into `photoIds`. The
 * row, its notes and the hold-for-options sheet are `CourtPhotos`, which the You tab's
 * *Photos* draws too ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2). What is left in this file is the step's own: its chrome, and *Continue*.
 *
 * **Two lines of small print are gone**: the line under the title, and the one under the row
 * saying that no photo is fine. Neither was untrue — the ceiling and the *or none at all*
 * are both in the eyebrow, and the continue control is never disabled, so a player who adds
 * nothing finds that out by pressing it rather than by being promised it in advance.
 */

import { useRouter } from 'expo-router';

import { useCurrentUser } from '@/features/auth/types';
import { Button, Note } from '@/shared/ui';

import { stepAfter } from '../domain/socialSteps';
import { useDraftPhotoBench, useProfilePhotos } from '../hooks/useProfilePhotos';

import { CourtPhotos } from './CourtPhotos';
import { CEILING_BODY, CEILING_TITLE, photosEyebrow } from './photoStepPresentation';
import { SocialStepLayout } from './SocialStepLayout';
import { SOCIAL_STEP_PATH } from './socialStepRoutes';
import { stepCopy } from './socialStepPresentation';

export function SocialPhotosStep() {
  const router = useRouter();
  const user = useCurrentUser();
  const workbench = useProfilePhotos(useDraftPhotoBench());

  // Where continuing leads is the step order's answer, not this screen's.
  const next = stepAfter('photos');

  return (
    <CourtPhotos workbench={workbench} posterOf={user.data?.id}>
      {(body, overlaid) => (
        <SocialStepLayout
          step="photos"
          eyebrow={photosEyebrow()}
          overlaid={overlaid}
          action={
            next === undefined ? null : (
              <>
                {workbench.standing.refusedAtTheCeiling ? (
                  // Pinned to the action bar rather than left beside the row, and announced:
                  // a player who picked a fourth may not be looking at the tiles, and a
                  // refusal they have to hunt for is a screen that did nothing.
                  <Note variant="amber" accessibilityRole="alert" title={CEILING_TITLE}>
                    {CEILING_BODY}
                  </Note>
                ) : null}

                {/* Never disabled. Photos are optional, and a control that made a player prove
                    they had none would be the step contradicting its own copy. */}
                <Button
                  label="Continue"
                  size="lg"
                  onPress={() => router.replace(SOCIAL_STEP_PATH[next])}
                  accessibilityHint={`Goes to ${stepCopy(next).title}`}
                />
              </>
            )
          }
        >
          {body}
        </SocialStepLayout>
      )}
    </CourtPhotos>
  );
}
