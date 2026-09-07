/**
 * Step two of onboarding's second part: **your court photos**.
 *
 * Up to three photos of the player on a court, or none. It is the one step of the seven that
 * can be finished without answering anything, and the screen says so before a player has to
 * work it out — a player who adds nothing gets a court poster generated from their own id,
 * which is what stops *optional* meaning *an empty box on your profile*.
 *
 * ## Nothing here decides anything
 *
 * The ceiling, the order, what promotion means and which ids reach the draft are
 * `photoCollection`'s, with their own tests and no renderer. Picking, the permission and
 * the upload queue are `useProfilePhotos`'. What is left in this file is what a player
 * sees — the same split the tags step made, and for the same reason: the profile editor
 * will obey these rules from a screen that looks nothing like this one.
 *
 * ## The ceiling is a fact of the layout
 *
 * The row is always three tiles. A filled tile shows its photo, the leftmost empty slot is
 * the add control, and at three photos there is no add control on screen at all — no
 * greyed-out plus, and no button that refuses when pressed (design-system 6.9). The refusal
 * in words exists for the other route to a fourth photo: a picker handing back more than the
 * row has room for, which the layout cannot say anything about on its own.
 *
 * ## Every photo is framed by the player before it is sent, and a held tile is how it is reframed
 *
 * The picker opens with the platform's crop frame, so what lands in a tile is what the player
 * chose to show rather than whatever the camera held. That has one consequence on this screen:
 * **a cropping pick answers with one picture**, so three photos is three presses of the add
 * control (`useProfilePhotos`).
 *
 * Past promote and remove, the tile has **no room for a third 44pt target** — so the rest is
 * behind a hold, which opens a sheet with three acts on that one picture: replace it, add
 * another beside it, or re-crop it. *Replace* and *Edit* reach the same picker, because there
 * is no way to re-crop a file the app already holds without a second native module, and the
 * copy on each control is what keeps them honest about that rather than the code pretending
 * they are different requests.
 *
 * **Remove is not on the sheet.** It is the square on the tile and stays there: the one
 * destructive act on this screen does not move behind a gesture nothing advertises.
 *
 * ## Uploads are one photo at a time, and a failure costs one photo
 *
 * Each tile carries its own progress and its own retry. Nothing about the row changes when
 * one fails — the other two keep their state, and pressing the red tile sends that one
 * again.
 *
 * ## The rule is stated once; the check speaks only when it has something to say
 *
 * The note at the top says what a photo is for and what it should show, and it does not
 * announce that anything is checked — announcing it to the majority whose photo is fine is
 * small print, and it reads as a threat to the rest. Every upload *is* checked, and a photo
 * the check did not read as on-court gets its own amber note under the row
 * (`photoStepPresentation`).
 *
 * **It is a warning and it is not a refusal.** A flagged photo is drawn like any other, it
 * keeps its place and its id, it goes into the commit, and `Continue` is not touched by it.
 * The check is wrong about some share of the photos it flags — nobody knows what share yet —
 * so the cost of being wrong has to be a sentence a player can disagree with.
 *
 * **Two lines of small print are gone**: the line under the title, and the one under the row
 * saying that no photo is fine. Neither was untrue — the ceiling and the *or none at all*
 * are both in the eyebrow, and the continue control is never disabled, so a player who adds
 * nothing finds that out by pressing it rather than by being promised it in advance.
 */

import { useRouter } from 'expo-router';
import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { useCurrentUser } from '@/features/auth/types';
import {
  BottomSheet,
  Button,
  Note,
  PhotoAddTile,
  PhotoPosterTile,
  PhotoRow,
  PhotoTile,
  theme,
  type PhotoTileFoot,
} from '@/shared/ui';

import { flaggedPositions, slotsLeft, type ProfilePhoto } from '../domain/photoCollection';
import { stepAfter } from '../domain/socialSteps';
import { useProfilePhotos } from '../hooks/useProfilePhotos';

import { courtPosterFor } from './courtPosterFraming';
import { SocialStepLayout } from './SocialStepLayout';
import { SOCIAL_STEP_PATH } from './socialStepRoutes';
import { stepCopy } from './socialStepPresentation';
import {
  ACCESS_BODY,
  ACCESS_TITLE,
  ADD_ANOTHER_ACTION,
  ADD_CONTROL_WORD,
  CEILING_BODY,
  CEILING_TITLE,
  EDIT_ACTION,
  FAILED_WORD,
  FLAGGED_BODY,
  PHOTO_OPTIONS_LINE,
  PHOTO_RULE_BODY,
  PHOTO_RULE_TITLE,
  PHOTO_SHEET_CLOSE,
  PHOTO_SHEET_TITLE,
  POSTER_LABEL,
  PROFILE_WORD,
  PROMOTE_LINE,
  REPLACE_ACTION,
  addControlLabel,
  flaggedNoticeTitle,
  optionsControlLabel,
  photoFailureMessage,
  photoTileHint,
  photoTileLabel,
  photosEyebrow,
  removeControlLabel,
  type PhotoAction,
} from './photoStepPresentation';

/**
 * Which of the strip's three occupants this photo has, and it is at most one.
 *
 * The order is the priority: an upload in flight and a failure are both about *right now*
 * and outrank the profile marker, which will still be true in a second. The `ink` border
 * carries that fact meanwhile, which is why the strip can give the slot away.
 */
function footFor(photo: ProfilePhoto, at: number): PhotoTileFoot {
  if (photo.upload.kind === 'uploading')
    return { kind: 'uploading', progress: photo.upload.progress };
  if (photo.upload.kind === 'failed') return { kind: 'failed', word: FAILED_WORD };
  return at === 0 ? { kind: 'profile', word: PROFILE_WORD } : { kind: 'none' };
}

export function SocialPhotosStep() {
  const router = useRouter();
  const user = useCurrentUser();
  const { photos, standing, add, replace, retry, promote, remove } = useProfilePhotos();

  /**
   * Which photo the sheet is about, held as its **uri** rather than its index.
   *
   * The index is a position in a list the sheet's own acts reorder: promoting from behind
   * the sheet, or a replacement landing, would leave a number pointing at a different
   * picture. The uri is the photo, which is what `photoCollection` already decided.
   */
  const [held, setHeld] = useState<string>();
  const heldAt = photos.findIndex((photo) => photo.uri === held);
  // Open only while the photo it is about is still in the row. Removing one from under the
  // sheet closes it rather than leaving three acts pointing at nothing.
  const sheetOpen = heldAt !== -1;

  /** Do the act, then close — a sheet that stayed up over a picker would be two overlays. */
  const actOn = (act: (uri: string) => void) => () => {
    const photo = held;
    setHeld(undefined);
    if (photo !== undefined) act(photo);
  };

  // Where continuing leads is the step order's answer, not this screen's.
  const next = stepAfter('photos');
  const room = slotsLeft(photos);
  // One reason per failed photo, because one failure costs one photo: two pictures refused
  // for different reasons are two things the player has to do something different about,
  // and a single message would name at most one of them.
  const failures = photos.flatMap((photo, at) =>
    photo.upload.kind === 'failed'
      ? [{ at, message: photoFailureMessage(photo.upload.error) }]
      : [],
  );
  // One note per flagged photo, for the reason there is one per failure: the sentence names
  // which tile it is about, and a single note over two of them would name neither.
  const flagged = flaggedPositions(photos);

  return (
    <>
      <SocialStepLayout
        step="photos"
        eyebrow={photosEyebrow()}
        overlaid={sheetOpen}
        action={
          next === undefined ? null : (
            <>
              {standing.refusedAtTheCeiling ? (
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
        <Note variant="info" title={PHOTO_RULE_TITLE}>
          {PHOTO_RULE_BODY}
        </Note>

        <PhotoRow style={s.row}>
          {/* The poster stands in the first slot only while there is no photo to lead —
              which is where a profile photo goes, and the whole of what it claims. */}
          {photos.length === 0 ? (
            <PhotoPosterTile
              key="poster"
              poster={user.data === undefined ? undefined : courtPosterFor(user.data.id)}
              accessibilityLabel={POSTER_LABEL}
            />
          ) : null}

          {photos.map((photo, at) => (
            <PhotoTile
              key={photo.uri}
              uri={photo.uri}
              profile={at === 0}
              foot={footFor(photo, at)}
              onPress={() =>
                photo.upload.kind === 'failed' ? retry(photo.uri) : promote(photo.uri)
              }
              // The three acts that are not promote and not remove, behind a hold. The
              // tile has room for two 44pt targets and both are taken (6.9), so this is
              // the gesture plus the accessibility action that stands in for it — and the
              // name says which photo, because three tiles would otherwise offer three
              // identical entries.
              options={{
                onLongPress: () => setHeld(photo.uri),
                accessibilityLabel: optionsControlLabel(at, photos.length),
              }}
              onRemove={() => remove(photo.uri)}
              accessibilityLabel={photoTileLabel(photo, at, photos.length)}
              accessibilityHint={photoTileHint(photo, at)}
              removeAccessibilityLabel={removeControlLabel(at, photos.length)}
            />
          ))}

          {room > 0 ? (
            <PhotoAddTile
              key="add"
              word={ADD_CONTROL_WORD}
              onPress={() => void add()}
              accessibilityLabel={addControlLabel(room)}
            />
          ) : null}
        </PhotoRow>

        {/* The promote line is drawn only where there is something to promote *to*; the
            hold is offered from the first photo, because replacing and re-cropping are
            acts on one picture and do not need a second. */}
        {photos.length > 1 ? <Text style={s.note}>{PROMOTE_LINE}</Text> : null}
        {photos.length > 0 ? <Text style={s.note}>{PHOTO_OPTIONS_LINE}</Text> : null}

        {standing.access !== 'granted' ? (
          <Note variant="amber" accessibilityRole="alert" title={ACCESS_TITLE[standing.access]}>
            {ACCESS_BODY[standing.access]}
          </Note>
        ) : null}

        {failures.map((failure) => (
          <Note
            key={failure.at}
            variant="coral"
            accessibilityRole="alert"
            title={photoTileLabel(photos[failure.at]!, failure.at, photos.length)}
          >
            {failure.message}
          </Note>
        ))}

        {/* Amber and not coral, and after the failures: a photo that did not arrive is
            something the player has to act on, and this is something they may ignore. [1.2]
            keeps coral for the five places it belongs, and a warning about a photo that is
            sitting right there in the row is not one of them. */}
        {flagged.map((at) => (
          <Note
            key={`flagged-${at}`}
            variant="amber"
            accessibilityRole="alert"
            title={flaggedNoticeTitle(at, photos.length)}
          >
            {FLAGGED_BODY}
          </Note>
        ))}
      </SocialStepLayout>

      {/* A **sibling** of the step, never a child: the layout spreads `behindOverlay` while
          this is up, and a sheet rendered inside that element would hide itself along with
          everything else.

          Its title names the photo it is about rather than repeating the sheet's own name,
          because the three acts below all say *this* and a player who held the second tile
          has to be able to check they held the one they meant. */}
      <BottomSheet
        visible={sheetOpen}
        onClose={() => setHeld(undefined)}
        title={
          heldAt === -1 ? PHOTO_SHEET_TITLE : photoTileLabel(photos[heldAt]!, heldAt, photos.length)
        }
        closeLabel={PHOTO_SHEET_CLOSE}
      >
        {/* Stacked full-width `secondary` buttons: three acts on one picture, none of them
            the accent (1.2), and none of them destructive — remove stays the square on the
            tile, where it has always been, rather than moving behind a gesture nobody can
            see.

            Every hint says what the control will actually do, and *Edit*'s is the one that
            has to: it opens the library rather than the photograph, because the crop frame
            only ever comes attached to choosing a picture (`photoStepPresentation`). */}
        <View style={s.actions}>
          <SheetAction action={REPLACE_ACTION} onPress={actOn(replace)} />
          <SheetAction action={ADD_ANOTHER_ACTION} onPress={actOn(() => void add())} />
          <SheetAction action={EDIT_ACTION} onPress={actOn(replace)} />
        </View>
      </BottomSheet>
    </>
  );
}

/** One act on the photo sheet. The words are `photoStepPresentation`'s, both of them. */
function SheetAction({
  action,
  onPress,
}: {
  readonly action: PhotoAction;
  readonly onPress: () => void;
}) {
  return (
    <Button
      label={action.label}
      variant="secondary"
      size="lg"
      accessibilityHint={action.hint}
      onPress={onPress}
    />
  );
}

const s = StyleSheet.create({
  row: { paddingTop: theme.space.xxs },
  /** Secondary text is always `tiny` in `muted` — what this step asks, and its two notes. */
  note: { ...theme.type.tiny, color: theme.color.muted },
  // Stacked, not a row: three labels side by side on a phone are three clipped words. The
  // gap is the one between stacked controls in an action group.
  actions: { gap: theme.space.sm },
});
