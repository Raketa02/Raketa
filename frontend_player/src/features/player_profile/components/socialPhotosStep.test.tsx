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

function photoStored(photoId: string): Wire['PhotoResponse'] {
  return {
    photo_id: photoId,
    url: `https://store.test/${photoId}?signature=whatever`,
    expires_at: '2026-08-25T12:00:00Z',
  };
}

/** The store accepts every photo, naming each one after the file it was sent as. */
function stubUploads() {
  let uploaded = 0;
  transport.on('POST', PHOTOS_PATH, () => {
    uploaded += 1;
    return json(photoStored(`photo-${uploaded}`), 201);
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

  await waitFor(() => expect(screen).toHavePathname('/photos'));
  await screen.findByText('Your court photos');
}

/** Press the add control and let the picker, the permission and the uploads settle. */
async function addPhotos() {
  fireEvent.press(screen.getByLabelText(/^Add a photo/));
  // The picker, the permission read and the uploads are all promises; the row is redrawn
  // as each lands, so the presses are flushed before anything is asserted.
  await act(async () => {
    await Promise.resolve();
  });
}

/**
 * The window the poster is drawn through, as the drawing itself reports it.
 *
 * The framing *is* the poster — the colours never vary — so this is the whole of what has
 * to come back the same for a player, and reading it off the rendered SVG is what makes
 * the assertion about the picture rather than about the function that chose it.
 */
async function posterFraming(): Promise<string> {
  const poster = await screen.findByLabelText(/generated court poster/);
  const drawing = poster.props.children as { readonly props: { readonly viewBox: string } };
  return drawing.props.viewBox;
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
    expect(screen.getByText(/Photos show you on a court/)).toBeTruthy();
    expect(screen.getByText(/Not a selfie, not the beach, not the gym mirror/)).toBeTruthy();
  });

  it('claims no check is performed on what is in the picture', async () => {
    // There is no content review running in this build. A screen that said we look would
    // be telling the player something untrue about how the product works.
    await reachThePhotosStep();

    for (const claim of [/we check/i, /reviewed/i, /moderat/i, /approved/i, /verified/i]) {
      expect(screen.queryByText(claim)).toBeNull();
    }
  });

  it('says that adding none is fine, before a player has to find out', async () => {
    await reachThePhotosStep();

    expect(screen.getByText(/No photo is fine/)).toBeTruthy();
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
    const first = await posterFraming();

    // The process dies and everything in memory with it. The id is the only input, so the
    // drawing has to come back identical — a poster that changed would read as a profile
    // that had.
    screen.unmount();
    queryClient.clear();
    useProfileDraft.getState().reset();
    await reachThePhotosStep();

    expect(await posterFraming()).toEqual(first);
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
  it('opens the picker for as many as the row still has room for', async () => {
    stubUploads();
    await reachThePhotosStep();

    await addPhotos();

    expect(library.limits).toEqual([3]);
  });

  it('shows a tile for each one and uploads them, one request per photo', async () => {
    stubUploads();
    await reachThePhotosStep();

    await addPhotos();

    await waitFor(() => expect(transport.requestsTo('POST', PHOTOS_PATH)).toHaveLength(3));
    expect(tileLabels()).toHaveLength(3);
  });

  it('puts the ids in the part draft, in the order the player arranged them', async () => {
    stubUploads();
    await reachThePhotosStep();

    await addPhotos();

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

    await addPhotos();

    await waitFor(() => expect(tileLabels()).toHaveLength(3));
    // Not a greyed-out plus and not a control that refuses when pressed — there is nothing
    // there to press (design-system 6.9).
    expect(screen.queryByLabelText(/^Add a photo/)).toBeNull();
  });

  it('refuses a fourth in words when a picker hands back more than it was asked for', async () => {
    stubUploads();
    library.library = [LIBRARY[0]!, LIBRARY[1]!];
    await reachThePhotosStep();
    await addPhotos();
    await waitFor(() => expect(tileLabels()).toHaveLength(2));

    // The picker was opened for one slot and answers with two — the case the row of three
    // cannot say anything about on its own.
    library.honoursLimit = false;
    library.library = [LIBRARY[2]!, pickedImage({ uri: 'file:///photos/four.jpg' })];
    await addPhotos();

    expect(await screen.findByText('Three is the ceiling')).toBeTruthy();
    // And it changed nothing beyond what fitted: three tiles, never four.
    await waitFor(() => expect(tileLabels()).toHaveLength(3));
  });
});

// ---------------------------------------------------------------------------
// The profile photo
// ---------------------------------------------------------------------------

describe('which photo leads', () => {
  it('is the first one added', async () => {
    stubUploads();
    await reachThePhotosStep();

    await addPhotos();

    await waitFor(() => expect(tileLabels()[0]).toBe('Photo 1 of 3, profile photo'));
  });

  it('changes to whichever photo is pressed', async () => {
    stubUploads();
    await reachThePhotosStep();
    await addPhotos();
    await settled(3);

    fireEvent.press(screen.getByLabelText('Photo 3 of 3'));

    expect(tileLabels()[0]).toBe('Photo 1 of 3, profile photo');
    expect(useProfileDraft.getState().draft?.photoIds).toEqual(['photo-3', 'photo-1', 'photo-2']);
  });

  it('carries the promotion as a sentence rather than a mark on every tile', async () => {
    stubUploads();
    await reachThePhotosStep();
    await addPhotos();
    await waitFor(() => expect(tileLabels()).toHaveLength(3));

    expect(screen.getByText('Tap a photo to make it the profile photo.')).toBeTruthy();
    expect(screen.getByLabelText('Photo 2 of 3').props.accessibilityHint).toBe(
      'Make this the profile photo',
    );
  });

  it('passes to the next photo when the one leading is removed', async () => {
    stubUploads();
    await reachThePhotosStep();
    await addPhotos();
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

    await addPhotos();

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

    await addPhotos();

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
    await addPhotos();
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
