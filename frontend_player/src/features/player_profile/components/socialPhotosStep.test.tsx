/**
 * The photos step, driven through the real route tree with the socket and the photo library
 * faked — and nothing else.
 *
 * Two edges are outside the app and both are described per test: the network, through
 * `installTransport`, and the device's photo library, through the app's **own port**. The
 * native module is never touched — it has no JS implementation a test could drive, which is
 * the whole reason `ImagePickingPort` exists. Everything between the two runs for real: the
 * router, the http client with its upload verb, the domain rules, the store and the screen.
 *
 * Every assertion is about what a player can see, what they can operate, or what an
 * assistive technology is told — **with one deliberate exception**. The part's draft is
 * read directly, because *photo ids and their order are held in the draft* is a requirement
 * of this step and there is nothing on screen that renders an id: the commit that would
 * make it observable is a later ticket. Waiting is never done that way — a barrier that
 * read the store would go green on a row that had not been redrawn — so `settled()` waits
 * on the tiles.
 */

import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';
import { Path, Stop } from 'react-native-svg';

import { refreshTokens } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  GATE_USER,
  launchSignedIn,
  resetImagePicking,
  stubGate as stubGateWith,
  stubImagePicking,
  stubProfileOptions,
} from '@/test-support/onboardingRouter';
import { fakeImagePicking, pickedImage, type FakeImagePicking } from '@/test-support/platform';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { PROFILE_PHOTO_ASPECT } from '../domain/photoCollection';
import { useProfileDraft } from '../store/profileDraft.store';

const PHOTOS_PATH = '/api/v1/photos';

/** One rating: the first part is behind this player, and the second one is not. */
const RATING: Wire['RatingResponse'] = {
  sport: 'PADEL',
  mu: 2.71,
  sigma: 0.62,
  confidence: 28,
  range: { low: 2.09, high: 3.33 },
  band: { name: 'Established', lower: 2.7, upper: 3.8 },
  status: 'initial_estimate',
  engine_version: 'racketskill-v3',
  updated_at: '2026-08-14T09:00:00Z',
};

/** Three pictures a player might choose, distinguishable by their URIs. */
const LIBRARY = [
  pickedImage({ uri: 'file:///photos/one.jpg', fileName: 'one.jpg' }),
  pickedImage({ uri: 'file:///photos/two.jpg', fileName: 'two.jpg' }),
  pickedImage({ uri: 'file:///photos/three.jpg', fileName: 'three.jpg' }),
];

let transport: Transport;
let library: FakeImagePicking;

function photoStored(
  photoId: string,
  review: Wire['PhotoResponse']['review'] = 'allowed',
): Wire['PhotoResponse'] {
  return {
    photo_id: photoId,
    url: `https://store.test/${photoId}?signature=whatever`,
    expires_at: '2026-08-25T12:00:00Z',
    review,
  };
}

/** The store accepts every photo, naming each one after the file it was sent as. */
function stubUploads(review: Wire['PhotoResponse']['review'] = 'allowed') {
  let uploaded = 0;
  transport.on('POST', PHOTOS_PATH, () => {
    uploaded += 1;
    return json(photoStored(`photo-${uploaded}`, review), 201);
  });
}

/** A launch by a player the gate owes the second part to, walked as far as step two. */
async function reachThePhotosStep() {
  stubGateWith(transport, { ratings: [RATING], hasPlayerProfile: false });
  stubProfileOptions(transport);
  stubImagePicking(library);

  await launchSignedIn();

  await waitFor(() => expect(screen).toHavePathname('/tags'));
  fireEvent.press(await screen.findByLabelText('Plays to win'));
  fireEvent.press(screen.getByLabelText('Here to improve'));
  fireEvent.press(await screen.findByLabelText('Continue'));
  await waitFor(() => expect(screen).toHavePathname('/intro'));

  // Nothing written: the intro is optional, and *Next* on an empty box carries none.
  fireEvent.press(screen.getByLabelText('Next'));
  await waitFor(() => expect(screen).toHavePathname('/photos'));
  await screen.findByText('Your court photos');
}

/**
 * Press the add control `times` over, letting the picker, the permission and the uploads
 * settle between presses.
 *
 * **One press is one photo.** Every pick goes through the platform's crop frame and a
 * cropping pick is single-select on both platforms, so a player who wants three presses
 * three times and the fake walks its library one picture per press — which is what the real
 * picker does. The picker, the permission read and the uploads are all promises and the row
 * is redrawn as each lands, so each press is flushed before the next.
 */
async function addPhotos(times = 1) {
  for (let press = 0; press < times; press += 1) {
    fireEvent.press(screen.getByLabelText(/^Add a photo/));
    await act(async () => {
      await Promise.resolve();
    });
  }
}

/**
 * The poster a player is looking at, as the drawing itself reports it.
 *
 * The hue and the pose *are* the poster — the composition never varies — so the two stops of
 * the ground and the figure's own paths are the whole of what has to come back the same, and
 * reading them off the rendered SVG is what makes the assertion about the picture rather
 * than about the function that chose it. The gradient's id is deliberately not read: it is a
 * per-instance value and a poster that came back with the same one would be the bug 6.9's
 * `useId()` rule exists to prevent.
 */
async function posterDrawing(): Promise<string> {
  await screen.findByLabelText(/generated court poster/);
  const ground = screen.UNSAFE_queryAllByType(Stop).map((stop) => stop.props.stopColor as string);
  const figure = screen.UNSAFE_queryAllByType(Path).map((path) => path.props.d as string);

  return [...ground, ...figure].join(' ');
}

/**
 * Wait until every tile has stopped saying it is uploading.
 *
 * Waiting on what the row *says* rather than on the store: the tiles are what a player
 * watches, and a barrier that read the draft would go green on a screen that had not been
 * redrawn.
 */
async function settled(held: number): Promise<void> {
  await waitFor(() =>
    expect(tileLabels()).toEqual(
      Array.from({ length: held }, (_unused, at) =>
        at === 0 ? `Photo 1 of ${held}, profile photo` : `Photo ${at + 1} of ${held}`,
      ),
    ),
  );
}

function tileLabels(): string[] {
  return screen
    .getAllByRole('button')
    .map((node) => String(node.props.accessibilityLabel))
    .filter((label) => label.startsWith('Photo '));
}

beforeEach(async () => {
  transport = installTransport();
  library = fakeImagePicking({ library: LIBRARY });
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  useProfileDraft.getState().reset();
});

afterEach(() => {
  transport.restore();
  resetImagePicking();
  queryClient.clear();
});

// ---------------------------------------------------------------------------
// What the screen says
// ---------------------------------------------------------------------------

describe('the words on the step', () => {
  it('states the on-court rule', async () => {
    await reachThePhotosStep();

    expect(screen.getByText('Rackets mandatory, faces optional')).toBeTruthy();
    expect(screen.getByText(/keep it about the racket sports/)).toBeTruthy();
    expect(screen.getByText(/no casual selfies, party photos, or gym mirrors/)).toBeTruthy();
  });

  it('does not announce the check to a player it has nothing to say to', async () => {
    // Every upload *is* checked now. Saying so up front is small print for the majority
    // whose photo is fine and reads as a threat to the rest — the same argument that took
    // the third line off this step. The check earns a sentence at the one moment it has a
    // claim to make, and this player has not uploaded anything.
    await reachThePhotosStep();

    for (const claim of [/we check/i, /reviewed/i, /moderat/i, /approved/i, /verified/i]) {
      expect(screen.queryByText(claim)).toBeNull();
    }
  });

  it('does not promise in advance that adding none is fine', async () => {
    // Two lines of small print are gone — the one under the title and the one under the
    // row. The eyebrow already says *up to three*, and the continue control is never
    // disabled, so a player who adds nothing finds that out by pressing it. What carrying
    // on without any actually gets you is said in the permission notes, at the one moment
    // somebody is deciding it.
    await reachThePhotosStep();

    expect(screen.queryByText(/No photo is fine/)).toBeNull();
    expect(screen.queryByText(/Up to three photos of you on a court/)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// The player with no photos
// ---------------------------------------------------------------------------

describe('a player who adds none', () => {
  it('is shown a generated court poster rather than an empty box', async () => {
    await reachThePhotosStep();

    expect(await screen.findByLabelText(/generated court poster, not a photograph/)).toBeTruthy();
  });

  it('keeps the add control where it is while the poster is still being drawn', async () => {
    // The poster's place in the row is decided by there being no photograph, not by who
    // the player is having been read — so the slot is there from the first frame and the
    // control beside it does not move out from under a finger.
    await reachThePhotosStep();
    const beforeTheDrawing = screen.getByLabelText(/^Add a photo/).props.accessibilityLabel;

    await screen.findByLabelText(/generated court poster/);

    expect(screen.getByLabelText(/^Add a photo/).props.accessibilityLabel).toBe(beforeTheDrawing);
  });

  it('can continue to the next step', async () => {
    await reachThePhotosStep();

    fireEvent.press(screen.getByLabelText('Continue'));

    await waitFor(() => expect(screen).toHavePathname('/availability'));
    expect(useProfileDraft.getState().draft?.photoIds).toEqual([]);
  });

  it('gets the same poster on the next launch, because it is a hash of who they are', async () => {
    await reachThePhotosStep();
    const first = await posterDrawing();
    // An empty read would make every assertion below vacuously true, which is exactly what
    // the retired viewBox check had become once the composition stopped varying.
    expect(first).not.toBe('');

    // The process dies and everything in memory with it. The id is the only input, so the
    // drawing has to come back identical — a poster that changed would read as a profile
    // that had.
    screen.unmount();
    queryClient.clear();
    useProfileDraft.getState().reset();
    await reachThePhotosStep();

    expect(await posterDrawing()).toEqual(first);
  });

  it('is not shown one once a photo of their own leads', async () => {
    stubUploads();
    library.library = [LIBRARY[0]!];
    await reachThePhotosStep();

    await addPhotos();

    expect(screen.queryByLabelText(/generated court poster/)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Adding photos
// ---------------------------------------------------------------------------

describe('adding photos from the device', () => {
  it('opens the picker for as many as the row still has room for, with the crop frame', async () => {
    stubUploads();
    await reachThePhotosStep();

    await addPhotos();

    // The room is what the picker is *opened with*, whatever a crop frame then does to it:
    // the ceiling is one rule, and a caller shrinking the number to match the platform
    // would be the ceiling stated in two places that could disagree.
    expect(library.limits).toEqual([3]);
    // And the frame itself, which is otherwise invisible — a cropped picture and an
    // uncropped one arrive looking the same, so nothing the row draws could prove it.
    expect(library.crops).toEqual([PROFILE_PHOTO_ASPECT]);
  });

  it('takes one photo per press, because a cropping pick answers with one', async () => {
    // The platform constraint, visible on the screen: `allowsEditing` is single-select on
    // both, so three photos is three presses rather than one multi-select. The row keeps
    // count in words as it fills.
    stubUploads();
    await reachThePhotosStep();

    await addPhotos();
    await settled(1);
    expect(screen.getByLabelText('Add a photo, 2 slots left')).toBeTruthy();

    await addPhotos();
    await settled(2);
    expect(screen.getByLabelText('Add a photo, 1 slot left')).toBeTruthy();

    expect(library.limits).toEqual([3, 2]);
  });

  it('shows a tile for each one and uploads them, one request per photo', async () => {
    stubUploads();
    await reachThePhotosStep();

    await addPhotos(3);

    await waitFor(() => expect(transport.requestsTo('POST', PHOTOS_PATH)).toHaveLength(3));
    expect(tileLabels()).toHaveLength(3);
  });

  it('puts the ids in the part draft, in the order the player arranged them', async () => {
    stubUploads();
    await reachThePhotosStep();

    await addPhotos(3);

    await waitFor(() =>
      expect(useProfileDraft.getState().draft?.photoIds).toEqual(['photo-1', 'photo-2', 'photo-3']),
    );
  });

  it('asks the OS for the library the first time, and just in time', async () => {
    stubUploads();
    await reachThePhotosStep();

    // Never at launch and never on arrival: the prompt appears when the player has said
    // what they want it for, by pressing the control.
    expect(library.state).toBe('undetermined');

    await addPhotos();

    expect(library.state).toBe('granted');
  });
});

describe('an upload still in flight', () => {
  it('says so on its own tile, and the row goes on working around it', async () => {
    let answer = (_response: Wire['PhotoResponse']) => {};
    transport.on(
      'POST',
      PHOTOS_PATH,
      () =>
        new Promise<Response>((resolve) => {
          answer = (response) => resolve(json(response, 201));
        }),
    );
    library.library = [LIBRARY[0]!];
    await reachThePhotosStep();

    await addPhotos();

    // The strip carries the bar and the bar is not legible to a screen reader, so the tile
    // says what it is doing (design-system 6.9).
    expect(await screen.findByLabelText('Photo 1 of 1, uploading')).toBeTruthy();
    // Nothing has an id yet, so nothing is claimed in the draft.
    expect(useProfileDraft.getState().draft?.photoIds).toEqual([]);
    // And the row still offers the next slot rather than waiting.
    expect(screen.getByLabelText('Add a photo, 2 slots left')).toBeTruthy();

    await act(async () => {
      answer(photoStored('photo-1'));
    });

    await waitFor(() => expect(screen.getByLabelText('Photo 1 of 1, profile photo')).toBeTruthy());
    expect(useProfileDraft.getState().draft?.photoIds).toEqual(['photo-1']);
  });
});

// ---------------------------------------------------------------------------
// The ceiling
// ---------------------------------------------------------------------------

describe('the ceiling', () => {
  it('is the layout: at three photos there is no add control at all', async () => {
    stubUploads();
    await reachThePhotosStep();

    await addPhotos(3);

    await waitFor(() => expect(tileLabels()).toHaveLength(3));
    // Not a greyed-out plus and not a control that refuses when pressed — there is nothing
    // there to press (design-system 6.9).
    expect(screen.queryByLabelText(/^Add a photo/)).toBeNull();
  });

  it('refuses a fourth in words when a picker hands back more than it was asked for', async () => {
    stubUploads();
    library.library = [LIBRARY[0]!, LIBRARY[1]!];
    await reachThePhotosStep();
    await addPhotos(2);
    await waitFor(() => expect(tileLabels()).toHaveLength(2));

    // The picker was opened for one slot, with a crop frame that is single-select on both
    // platforms, and answers with two anyway — the case the row of three cannot say
    // anything about on its own. Both limits are honoured on the far side of a boundary
    // this app does not own, so neither may be assumed.
    library.honoursLimit = false;
    library.library = [LIBRARY[2]!, pickedImage({ uri: 'file:///photos/four.jpg' })];
    await addPhotos();

    expect(await screen.findByText('Three is the ceiling')).toBeTruthy();
    // And it changed nothing beyond what fitted: three tiles, never four.
    await waitFor(() => expect(tileLabels()).toHaveLength(3));
  });
});

// ---------------------------------------------------------------------------
// The sheet a held tile opens
// ---------------------------------------------------------------------------

/**
 * Hold a tile the way a player does, and let the sheet arrive.
 *
 * `fireEvent` is given the real gesture rather than the accessibility action, because the
 * gesture is what almost everybody uses. That the action reaches the same place is its own
 * test below.
 */
async function holdPhoto(label: string) {
  fireEvent(screen.getByLabelText(label), 'longPress');
  await screen.findByLabelText('Close photo options');
}

/** Press one of the sheet's three acts and let the picker and the upload settle. */
async function pressAction(label: string) {
  fireEvent.press(screen.getByLabelText(label));
  await act(async () => {
    await Promise.resolve();
  });
}

describe('holding a photo', () => {
  it('offers three acts on that photo, and says which photo it is about', async () => {
    stubUploads();
    await reachThePhotosStep();
    await addPhotos(2);
    await settled(2);

    await holdPhoto('Photo 2 of 2');

    // The sheet names the photo rather than repeating its own name: the three acts all say
    // *this*, so a player who held the second tile has to be able to check they held the
    // one they meant.
    expect(screen.getByText('Photo 2 of 2')).toBeTruthy();
    expect(screen.getByLabelText('Replace this photo')).toBeTruthy();
    expect(screen.getByLabelText('Add new photo')).toBeTruthy();
    expect(screen.getByLabelText('Edit')).toBeTruthy();
  });

  /**
   * The one thing the sheet has to be honest about. *Replace* and *Edit* reach the same
   * picker because there is no way to re-crop a file the app already holds without a second
   * native module — so a player who taps *Edit* expecting their photograph in a crop frame
   * will be looking at their library, and the hint is the only place they can be told that
   * before it happens.
   */
  it('says of Edit that it opens the library, because that is what re-cropping costs', async () => {
    stubUploads();
    await reachThePhotosStep();
    await addPhotos();
    await settled(1);

    await holdPhoto('Photo 1 of 1, profile photo');

    expect(screen.getByLabelText('Edit').props.accessibilityHint).toBe(
      'Opens your photos so you can choose this one again and re-crop it',
    );
    expect(screen.getByLabelText('Replace this photo').props.accessibilityHint).toBe(
      'Choose a different photo for this spot, and crop it',
    );
  });

  /**
   * The whole reason the tile carries an accessibility action beside the gesture: a screen
   * reader cannot hold a control down, and nothing on the tile advertises that holding it
   * does anything.
   */
  it('is reachable without the gesture, by an action that names which photo', async () => {
    stubUploads();
    await reachThePhotosStep();
    await addPhotos(2);
    await settled(2);

    const tile = screen.getByLabelText('Photo 2 of 2');
    expect(tile.props.accessibilityActions).toEqual([
      { name: 'longpress', label: 'Options for photo 2 of 2' },
    ]);

    fireEvent(tile, 'accessibilityAction', { nativeEvent: { actionName: 'longpress' } });

    expect(await screen.findByLabelText('Close photo options')).toBeTruthy();
  });

  it('says under the row that the hold is there at all, once there is a photo to hold', async () => {
    stubUploads();
    await reachThePhotosStep();

    // Nothing to hold, so nothing is offered — the same shape the promote line has.
    expect(screen.queryByText('Press and hold a photo to replace, add or edit.')).toBeNull();

    await addPhotos();
    await settled(1);

    expect(screen.getByText('Press and hold a photo to replace, add or edit.')).toBeTruthy();
  });

  it('closes without doing anything when the sheet is dismissed', async () => {
    stubUploads();
    await reachThePhotosStep();
    await addPhotos();
    await settled(1);

    await holdPhoto('Photo 1 of 1, profile photo');
    fireEvent.press(screen.getByLabelText('Close photo options'));

    await waitFor(() => expect(screen.queryByLabelText('Close photo options')).toBeNull());
    expect(tileLabels()).toEqual(['Photo 1 of 1, profile photo']);
    expect(library.limits).toEqual([3]);
  });
});

describe('replacing a photo from the sheet', () => {
  it('puts the new picture in the slot the old one held, and sends it', async () => {
    stubUploads();
    await reachThePhotosStep();
    await addPhotos(2);
    await settled(2);
    await waitFor(() =>
      expect(useProfileDraft.getState().draft?.photoIds).toEqual(['photo-1', 'photo-2']),
    );

    // The player picks the third picture as the replacement for the first.
    library.library = [LIBRARY[2]!];
    await holdPhoto('Photo 1 of 2, profile photo');
    await pressAction('Replace this photo');

    // Still two photos, and the replacement is leading — a remove and an add would have
    // sent it to the back.
    await waitFor(() => expect(useProfileDraft.getState().photos).toHaveLength(2));
    expect(useProfileDraft.getState().photos[0]?.uri).toBe(LIBRARY[2]!.uri);
    await waitFor(() =>
      expect(useProfileDraft.getState().draft?.photoIds).toEqual(['photo-3', 'photo-2']),
    );
  });

  it('opens the picker for one slot, with the crop frame, even at the ceiling', async () => {
    // A replacement takes a position that is already occupied, so the room the row has left
    // is not the number it asks for — and a full row can still take one.
    stubUploads();
    await reachThePhotosStep();
    await addPhotos(3);
    await settled(3);

    library.library = [pickedImage({ uri: 'file:///photos/four.jpg' })];
    await holdPhoto('Photo 1 of 3, profile photo');
    await pressAction('Replace this photo');

    expect(library.limits).toEqual([3, 2, 1, 1]);
    expect(library.crops[3]).toEqual(PROFILE_PHOTO_ASPECT);
    // The ceiling is untouched: three in, three out, and no refusal.
    await waitFor(() => expect(tileLabels()).toHaveLength(3));
    expect(screen.queryByText('Three is the ceiling')).toBeNull();
  });

  it('changes nothing when the player backs out of the picker', async () => {
    stubUploads();
    await reachThePhotosStep();
    await addPhotos();
    await settled(1);

    library.library = [];
    await holdPhoto('Photo 1 of 1, profile photo');
    await pressAction('Replace this photo');

    await waitFor(() => expect(screen.queryByLabelText('Close photo options')).toBeNull());
    expect(tileLabels()).toEqual(['Photo 1 of 1, profile photo']);
    expect(useProfileDraft.getState().draft?.photoIds).toEqual(['photo-1']);
  });

  it('adds beside it instead when that is the act chosen', async () => {
    stubUploads();
    await reachThePhotosStep();
    await addPhotos();
    await settled(1);

    await holdPhoto('Photo 1 of 1, profile photo');
    await pressAction('Add new photo');

    // Two photos now, and the one that was held still leads — adding beside something is
    // not replacing it.
    await settled(2);
    expect(useProfileDraft.getState().photos[0]?.uri).toBe(LIBRARY[0]!.uri);
    await waitFor(() =>
      expect(useProfileDraft.getState().draft?.photoIds).toEqual(['photo-1', 'photo-2']),
    );
  });
});

// ---------------------------------------------------------------------------
// The profile photo
// ---------------------------------------------------------------------------

describe('which photo leads', () => {
  it('is the first one added', async () => {
    stubUploads();
    await reachThePhotosStep();

    await addPhotos(3);

    await waitFor(() => expect(tileLabels()[0]).toBe('Photo 1 of 3, profile photo'));
  });

  it('changes to whichever photo is pressed', async () => {
    stubUploads();
    await reachThePhotosStep();
    await addPhotos(3);
    await settled(3);

    fireEvent.press(screen.getByLabelText('Photo 3 of 3'));

    expect(tileLabels()[0]).toBe('Photo 1 of 3, profile photo');
    expect(useProfileDraft.getState().draft?.photoIds).toEqual(['photo-3', 'photo-1', 'photo-2']);
  });

  it('carries the promotion as a sentence rather than a mark on every tile', async () => {
    stubUploads();
    await reachThePhotosStep();
    await addPhotos(3);
    await waitFor(() => expect(tileLabels()).toHaveLength(3));

    expect(screen.getByText('Tap a photo to make it the profile photo.')).toBeTruthy();
    expect(screen.getByLabelText('Photo 2 of 3').props.accessibilityHint).toBe(
      'Make this the profile photo',
    );
  });

  it('passes to the next photo when the one leading is removed', async () => {
    stubUploads();
    await reachThePhotosStep();
    await addPhotos(3);
    await settled(3);

    fireEvent.press(screen.getByLabelText('Remove photo 1 of 3'));

    expect(tileLabels()[0]).toBe('Photo 1 of 2, profile photo');
    expect(useProfileDraft.getState().draft?.photoIds).toEqual(['photo-2', 'photo-3']);
  });
});

// ---------------------------------------------------------------------------
// One upload failing
// ---------------------------------------------------------------------------

describe('an upload that fails', () => {
  it('costs one photo rather than the row, and offers that photo a retry', async () => {
    let attempts = 0;
    transport.on('POST', PHOTOS_PATH, () => {
      attempts += 1;
      // The second photo of three, and only the first time it is sent.
      if (attempts === 2) return errorResponse(503, 'upstream_unavailable');
      return json(photoStored(`photo-${attempts}`), 201);
    });
    await reachThePhotosStep();

    await addPhotos(3);

    await waitFor(() => expect(screen.getByLabelText('Photo 2 of 3, upload failed')).toBeTruthy());
    // Nothing about the other two changed.
    expect(screen.getByLabelText('Photo 1 of 3, profile photo')).toBeTruthy();
    expect(screen.getByLabelText('Photo 3 of 3')).toBeTruthy();
    expect(screen.getByLabelText('Photo 2 of 3, upload failed').props.accessibilityHint).toBe(
      'Try this upload again',
    );
  });

  it('sends only that photo again when its tile is pressed', async () => {
    let attempts = 0;
    transport.on('POST', PHOTOS_PATH, () => {
      attempts += 1;
      if (attempts === 1) return errorResponse(503, 'upstream_unavailable');
      return json(photoStored(`photo-${attempts}`), 201);
    });
    library.library = [LIBRARY[0]!];
    await reachThePhotosStep();
    await addPhotos();
    await waitFor(() => expect(screen.getByLabelText('Photo 1 of 1, upload failed')).toBeTruthy());

    fireEvent.press(screen.getByLabelText('Photo 1 of 1, upload failed'));

    await waitFor(() => expect(useProfileDraft.getState().draft?.photoIds).toEqual(['photo-2']));
    expect(transport.requestsTo('POST', PHOTOS_PATH)).toHaveLength(2);
  });

  it('says why, in words the player can act on rather than the backend diagnostic', async () => {
    transport.on('POST', PHOTOS_PATH, () =>
      errorResponse(400, 'unsupported_image_format', 'declared media type not accepted'),
    );
    library.library = [LIBRARY[0]!];
    await reachThePhotosStep();

    await addPhotos();

    expect(await screen.findByText(/That format is not one we can take/)).toBeTruthy();
    expect(screen.queryByText('declared media type not accepted')).toBeNull();
  });

  it('names a reason per photo, because two failures are two different things to do', async () => {
    let attempts = 0;
    transport.on('POST', PHOTOS_PATH, () => {
      attempts += 1;
      return attempts === 1
        ? errorResponse(400, 'unsupported_image_format')
        : errorResponse(413, 'image_too_large');
    });
    library.library = [LIBRARY[0]!, LIBRARY[1]!];
    await reachThePhotosStep();

    await addPhotos(2);

    expect(await screen.findByText(/That format is not one we can take/)).toBeTruthy();
    expect(await screen.findByText(/That photo is too large/)).toBeTruthy();
    // Each says which photo it is about — there are two red tiles and two sentences.
    expect(screen.getAllByText(/Photo \d of 2, upload failed/)).toHaveLength(2);
  });

  it('never blocks continuing — the photo is optional whether or not it arrived', async () => {
    transport.on('POST', PHOTOS_PATH, () => errorResponse(503, 'upstream_unavailable'));
    library.library = [LIBRARY[0]!];
    await reachThePhotosStep();
    await addPhotos();
    await waitFor(() => expect(screen.getByLabelText('Photo 1 of 1, upload failed')).toBeTruthy());

    fireEvent.press(screen.getByLabelText('Continue'));

    await waitFor(() => expect(screen).toHavePathname('/availability'));
    // A photo that never arrived has no id, so nothing unresolvable reaches the draft.
    expect(useProfileDraft.getState().draft?.photoIds).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// The permission
// ---------------------------------------------------------------------------

describe('a player who refuses the photo library', () => {
  it('can still finish the step', async () => {
    library = fakeImagePicking({ answer: 'denied', library: [] });
    await reachThePhotosStep();

    await addPhotos();

    fireEvent.press(screen.getByLabelText('Continue'));
    await waitFor(() => expect(screen).toHavePathname('/availability'));
  });

  it('is told what happened and that pressing again asks once more', async () => {
    library = fakeImagePicking({ answer: 'denied', library: [] });
    await reachThePhotosStep();

    await addPhotos();

    expect(await screen.findByText('Raketa has no access to your photos')).toBeTruthy();
    expect(screen.getByText(/Press Add a photo again to allow it/)).toBeTruthy();
  });

  it('is sent to Settings instead when the refusal is permanent', async () => {
    // A blocked permission resolves instantly and negatively without showing anything, so
    // "press it again" would be advice that cannot work.
    library = fakeImagePicking({ state: 'blocked', answer: 'granted', library: [] });
    await reachThePhotosStep();

    await addPhotos();

    expect(await screen.findByText('Photo access is turned off')).toBeTruthy();
    expect(screen.getByText(/Turn it on for Raketa in Settings/)).toBeTruthy();
  });

  it('is told nothing at all when they simply backed out of the picker', async () => {
    library = fakeImagePicking({ answer: 'granted', library: [] });
    await reachThePhotosStep();

    await addPhotos();

    expect(screen.queryByText(/no access to your photos/)).toBeNull();
    expect(screen.queryByText(/Photo access is turned off/)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// The draft
// ---------------------------------------------------------------------------

describe('the photos a player walks away from', () => {
  it('are still there when they walk back', async () => {
    stubUploads();
    await reachThePhotosStep();
    await addPhotos(3);
    await settled(3);

    fireEvent.press(screen.getByLabelText('Continue'));
    await waitFor(() => expect(screen).toHavePathname('/availability'));
    fireEvent.press(screen.getByLabelText('Back to Your court photos'));
    await waitFor(() => expect(screen).toHavePathname('/photos'));

    expect(tileLabels()).toEqual(['Photo 1 of 3, profile photo', 'Photo 2 of 3', 'Photo 3 of 3']);
  });
});

describe('who the poster is drawn for', () => {
  it('is the signed-in player, read once through the auth feature rather than twice', async () => {
    await reachThePhotosStep();

    expect(await screen.findByLabelText(/generated court poster/)).toBeTruthy();
    // The gate already asked who this is; the step must not invent a second read of the
    // same route under a second key.
    expect(GATE_USER.id).toBeTruthy();
    expect(
      transport.requests.filter((request) => request.path === '/api/v1/users/me').length,
    ).toBeLessThanOrEqual(2);
  });
});

// ---------------------------------------------------------------------------
// A photo the on-court check did not read as on-court
// ---------------------------------------------------------------------------

describe('a flagged photo', () => {
  it('is warned about by name, and the warning is announced', async () => {
    // Announced rather than left beside the row: the player is looking at a picture they
    // just chose, not at the space under it, and a warning they have to hunt for is a
    // screen that did nothing.
    stubUploads('flagged');
    library.library = [LIBRARY[0]!, LIBRARY[1]!];
    await reachThePhotosStep();

    await addPhotos(2);
    await settled(2);

    const warnings = await screen.findAllByText(/we could not see a court/);
    expect(warnings.map((node) => String(node.props.children))).toEqual([
      'Photo 1 of 2 — we could not see a court',
      'Photo 2 of 2 — we could not see a court',
    ]);
    // One note per flagged photo, each one an alert: a single note over two of them would
    // name neither, which is the same reason there is one per failure.
    expect(screen.getAllByRole('alert')).toHaveLength(2);
    expect(screen.getAllByText(/Nothing is blocked/)).toHaveLength(2);
  });

  it('is kept, keeps its place, and goes into the draft like any other', async () => {
    // The whole of the rule the backend ships: it warns and it never refuses. A false
    // positive costs a sentence, not a photograph and not a signup.
    stubUploads('flagged');
    library.library = [LIBRARY[0]!];
    await reachThePhotosStep();

    await addPhotos();
    await settled(1);

    expect(tileLabels()).toEqual(['Photo 1 of 1, profile photo']);
    expect(useProfileDraft.getState().draft?.photoIds).toEqual(['photo-1']);
  });

  it('does not stand between the player and the next step', async () => {
    stubUploads('flagged');
    library.library = [LIBRARY[0]!];
    await reachThePhotosStep();
    await addPhotos();
    await settled(1);

    fireEvent.press(screen.getByLabelText('Continue'));

    await waitFor(() => expect(screen).toHavePathname('/availability'));
    expect(useProfileDraft.getState().draft?.photoIds).toEqual(['photo-1']);
  });

  it('stops being warned about the moment it is removed', async () => {
    // The note is derived from the row rather than held beside it, so removing the photo
    // takes its sentence with it — a warning still on screen about a picture that is gone
    // is a warning that lies.
    stubUploads('flagged');
    library.library = [LIBRARY[0]!];
    await reachThePhotosStep();
    await addPhotos();
    await settled(1);

    fireEvent.press(screen.getByLabelText('Remove photo 1 of 1'));

    await waitFor(() => expect(screen.queryByText(/we could not see a court/)).toBeNull());
  });

  it('is not what an allowed photo gets', async () => {
    stubUploads('allowed');
    library.library = [LIBRARY[0]!];
    await reachThePhotosStep();

    await addPhotos();
    await settled(1);

    expect(screen.queryByText(/we could not see a court/)).toBeNull();
  });

  it('is not what a photo still going up gets, nor one that failed', async () => {
    // Neither has an answer from the platform: one has not been looked at yet and the
    // other was never stored. A tile that warned on either would be inventing a verdict.
    transport.on('POST', PHOTOS_PATH, () => errorResponse(500, 'server_error', 'nope'));
    library.library = [LIBRARY[0]!];
    await reachThePhotosStep();

    await addPhotos();

    await screen.findByLabelText('Photo 1 of 1, upload failed');
    expect(screen.queryByText(/we could not see a court/)).toBeNull();
  });
});
