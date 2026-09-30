/**
 * **Photos, Tags and Intro edited from You, walked the way a player walks them** — the real
 * route tree, the real bar, and only `fetch` and the photo library faked
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2, §6; [#471](https://github.com/Raketa02/Raketa/issues/471)).
 *
 * Each screen is an onboarding step's control under the tab's chrome, and the steps' own
 * suites already prove the controls — the ceiling, the picker, the counter. What is proved
 * here is what the tab added: each screen **draws from the read**; the photos **write on every
 * change** — a promotion, a removal, an upload that landed — where the tags and the intro are
 * a draft until *Save*; the intro's three refusals land where they land; and the row's live
 * line follows the cache on the way back. And, since 2026-09-18, that a *Save* with nothing to
 * send is drawn green and saying *Saved* — and an ask under the floor is not.
 */

import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { doorRowLabel, theme } from '@/shared/ui';
import { fillOf } from '@/test-support/drawn';
import {
  OWN_RECORD_PATH,
  PROFILE_OPTIONS_SERVED,
  PROFILE_SURFACE_SERVED,
  launchSignedIn,
  resetImagePicking,
  stubGate,
  stubImagePicking,
  stubInterest,
  stubOwnRecord,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import { fakeImagePicking, pickedImage, type FakeImagePicking } from '@/test-support/platform';
import {
  errorResponse,
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { INTRO_CAP } from '../domain/intro';

import { INTRO_FIELD_LABEL, INTRO_REFUSAL_SENTENCE } from './introPresentation';
import {
  ADD_ANOTHER_ACTION,
  EDIT_ACTION,
  FLAGGED_BODY,
  PHOTOS_RULE,
  PHOTO_RULE_TITLE,
  PROMOTE_LINE,
  REPLACE_ACTION,
  flaggedNoticeTitle,
} from './photoStepPresentation';
import { stepCopy } from './socialStepPresentation';
import { socialTagCeilingTitle } from './socialTagPresentation';
import {
  INTRO_TITLE,
  NO_INTRO_LINE,
  PHOTOS_TITLE,
  REMOVE_INTRO,
  SAVE,
  SAVED,
  TAGS_TITLE,
  TRY_AGAIN,
  YOUR_WEEK_TITLE,
  introLine,
  photosLine,
  tagsLine,
  weekLine,
} from './youProfilePresentation';

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

const PHOTOS_PATH = '/api/v1/players/me/photos';
const TAGS_PATH = '/api/v1/players/me/social-tags';
const INTRO_PATH = '/api/v1/players/me/intro';
const UPLOAD_PATH = '/api/v1/photos';

/** The two photos the served profile holds: the first passed the check, the second was flagged. */
const HELD = PROFILE_SURFACE_SERVED.photos;
const HELD_IDS = HELD.map((photo) => photo.photo_id);
const MAXIMUM_TAGS = PROFILE_OPTIONS_SERVED.social_tag_selection.maximum_tags;

let transport: Transport;
let library: FakeImagePicking;

/** `GET /photos/{id}` for each held photo — the signed address a restored tile draws. */
function stubAddresses(ids: readonly string[] = HELD_IDS) {
  for (const id of ids) {
    transport.on('GET', `${UPLOAD_PATH}/${id}`, () =>
      json<Wire['PhotoResponse']>({
        photo_id: id,
        url: `https://store.test/${id}?signature=whatever`,
        expires_at: '2026-08-25T12:00:00Z',
        review: null,
      }),
    );
  }
}

/** The photos write answers with the ids as sent — the route keeps the player's order. */
function stubPhotosWrite() {
  transport.on('PUT', PHOTOS_PATH, (request) =>
    json<Wire['PhotosResponse']>({
      photo_ids: (request.body as Wire['ChangePhotosRequest']).photo_ids,
    }),
  );
}

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [RATING], hasPlayerProfile: true });
  stubProfileSurface(transport);
  stubProfileOptions(transport);
  stubInterest(transport);
  stubOwnRecord(transport);
  stubAddresses();
  library = fakeImagePicking({
    state: 'granted',
    library: [pickedImage({ uri: 'file:///photos/three.jpg', fileName: 'three.jpg' })],
  });
  stubImagePicking(library);
});

afterEach(async () => {
  transport.restore();
  resetImagePicking();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

const TWO_SLOTS = weekLine([
  { day: 2, hour: 19 },
  { day: 6, hour: 9 },
]);

/** A signed-in player standing on the You tab, with the profile read in. */
async function onYou() {
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('You'));
  await screen.findByLabelText(doorRowLabel(YOUR_WEEK_TITLE, TWO_SLOTS));
}

const row = (title: string, line: string) => screen.getByLabelText(doorRowLabel(title, line));

/** The tiles, as a screen reader hears them, in the row's order. */
function tileLabels(): string[] {
  return screen
    .getAllByRole('button')
    .map((node) => String(node.props.accessibilityLabel))
    .filter((label) => label.startsWith('Photo '));
}

/** Let the picker, the permission, the upload and the write land, in that order. */
async function settle() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
  });
}

const puts = (path: string) => transport.requestsTo('PUT', path);

// ---------------------------------------------------------------------------
// Photos
// ---------------------------------------------------------------------------

describe('Photos', () => {
  const HELD_LINE = photosLine([
    { photoId: 'photo-held-1', review: 'allowed' },
    { photoId: 'photo-held-2' },
  ]);

  async function openThePhotos() {
    await onYou();
    fireEvent.press(row(PHOTOS_TITLE, HELD_LINE));
    await screen.findByRole('header', { name: stepCopy('photos').title });
    await screen.findByLabelText('Photo 1 of 2, profile photo');
  }

  it('draws the step’s row from the read: the tiles, the rule, the lines and the flagged notice', async () => {
    await openThePhotos();

    expect(screen.getByText(`On your card · ${PHOTOS_RULE}`)).toBeTruthy();
    expect(screen.getByText(PHOTO_RULE_TITLE)).toBeTruthy();
    expect(tileLabels()).toEqual(['Photo 1 of 2, profile photo', 'Photo 2 of 2']);
    expect(screen.getByLabelText('Add a photo, 1 slot left')).toBeTruthy();
    expect(screen.getByText(PROMOTE_LINE)).toBeTruthy();
    // The verdict the read served: the second was flagged, and the owner is told so here.
    expect(screen.getByText(flaggedNoticeTitle(1, 2))).toBeTruthy();
    expect(screen.getByText(FLAGGED_BODY)).toBeTruthy();
    // Each tile was drawn from its own signed address, and nothing was written on arrival.
    for (const id of HELD_IDS) {
      expect(transport.requestsTo('GET', `${UPLOAD_PATH}/${id}`)).toHaveLength(1);
    }
    expect(puts(PHOTOS_PATH)).toHaveLength(0);
    // And no *Continue*, and no *Save*: the row is the state.
    expect(screen.queryByLabelText('Continue')).toBeNull();
    expect(screen.queryByLabelText(SAVE)).toBeNull();
  });

  it('sends the ids in order on a promotion, and the row’s line follows', async () => {
    stubPhotosWrite();
    await openThePhotos();

    fireEvent.press(screen.getByLabelText('Photo 2 of 2'));

    await waitFor(() => expect(puts(PHOTOS_PATH)).toHaveLength(1));
    expect(puts(PHOTOS_PATH)[0]?.body).toEqual({ photo_ids: ['photo-held-2', 'photo-held-1'] });
    expect(tileLabels()).toEqual(['Photo 1 of 2, profile photo', 'Photo 2 of 2']);
    // The one that leads now was flagged, and the line says so.
    fireEvent.press(screen.getByLabelText('Back'));
    expect(
      await screen.findByLabelText(
        doorRowLabel(
          PHOTOS_TITLE,
          photosLine([{ photoId: 'photo-held-2', review: 'flagged' }, { photoId: 'photo-held-1' }]),
        ),
      ),
    ).toBeTruthy();
  });

  it('sends the ids left on a removal, and an empty list when the last one goes', async () => {
    stubPhotosWrite();
    await openThePhotos();

    fireEvent.press(screen.getByLabelText('Remove photo 2 of 2'));
    await waitFor(() => expect(puts(PHOTOS_PATH)).toHaveLength(1));
    expect(puts(PHOTOS_PATH)[0]?.body).toEqual({ photo_ids: ['photo-held-1'] });

    fireEvent.press(screen.getByLabelText('Remove photo 1 of 1'));
    await waitFor(() => expect(puts(PHOTOS_PATH)).toHaveLength(2));
    expect(puts(PHOTOS_PATH)[1]?.body).toEqual({ photo_ids: [] });
    // The poster stands in again.
    expect(await screen.findByLabelText(/generated court poster/)).toBeTruthy();

    fireEvent.press(screen.getByLabelText('Back'));
    expect(await screen.findByLabelText(doorRowLabel(PHOTOS_TITLE, photosLine([])))).toBeTruthy();
  });

  it('sends the write when an upload lands — and not before', async () => {
    stubPhotosWrite();
    transport.on('POST', UPLOAD_PATH, () =>
      json<Wire['PhotoResponse']>(
        {
          photo_id: 'photo-3',
          url: 'https://store.test/photo-3?signature=whatever',
          expires_at: '2026-08-25T12:00:00Z',
          review: 'allowed',
        },
        201,
      ),
    );
    await openThePhotos();

    fireEvent.press(screen.getByLabelText('Add a photo, 1 slot left'));
    await settle();

    await waitFor(() => expect(puts(PHOTOS_PATH)).toHaveLength(1));
    expect(transport.requestsTo('POST', UPLOAD_PATH)).toHaveLength(1);
    expect(puts(PHOTOS_PATH)[0]?.body).toEqual({
      photo_ids: ['photo-held-1', 'photo-held-2', 'photo-3'],
    });
    await waitFor(() => expect(tileLabels()).toHaveLength(3));

    fireEvent.press(screen.getByLabelText('Back'));
    expect(
      await screen.findByLabelText(
        doorRowLabel(
          PHOTOS_TITLE,
          photosLine([
            { photoId: 'photo-held-1', review: 'allowed' },
            { photoId: 'photo-held-2', review: 'flagged' },
            { photoId: 'photo-3', review: 'allowed' },
          ]),
        ),
      ),
    ).toBeTruthy();
  });

  it('writes nothing while a replacement is on its way, and the new id in place once it lands', async () => {
    stubPhotosWrite();
    // The upload is held open until the test lets it land.
    let land: (() => void) | undefined;
    const landed = new Promise<void>((resolve) => {
      land = resolve;
    });
    transport.on('POST', UPLOAD_PATH, async () => {
      await landed;
      return json<Wire['PhotoResponse']>(
        {
          photo_id: 'photo-3',
          url: 'https://store.test/photo-3?signature=whatever',
          expires_at: '2026-08-25T12:00:00Z',
          review: 'allowed',
        },
        201,
      );
    });
    await openThePhotos();

    fireEvent(screen.getByLabelText('Photo 1 of 2, profile photo'), 'longPress');
    await screen.findByLabelText('Close photo options');
    fireEvent.press(screen.getByLabelText(REPLACE_ACTION.label));
    await settle();

    // The slot shows the new picture on its way — and the profile still holds the old one.
    expect(await screen.findByLabelText('Photo 1 of 2, uploading')).toBeTruthy();
    expect(puts(PHOTOS_PATH)).toHaveLength(0);

    await act(async () => {
      land?.();
      await Promise.resolve();
    });

    await waitFor(() => expect(puts(PHOTOS_PATH)).toHaveLength(1));
    expect(puts(PHOTOS_PATH)[0]?.body).toEqual({ photo_ids: ['photo-3', 'photo-held-2'] });
  });

  it('leaves the profile holding the old photo when its replacement fails to arrive', async () => {
    stubPhotosWrite();
    transport.on('POST', UPLOAD_PATH, () => errorResponse(503, 'upstream_unavailable'));
    await openThePhotos();

    fireEvent(screen.getByLabelText('Photo 2 of 2'), 'longPress');
    await screen.findByLabelText('Close photo options');
    fireEvent.press(screen.getByLabelText(EDIT_ACTION.label));
    await settle();

    expect(await screen.findByLabelText('Photo 2 of 2, upload failed')).toBeTruthy();
    expect(puts(PHOTOS_PATH)).toHaveLength(0);
    // Removing the failed slot is a removal of the old photo, and that is written.
    fireEvent.press(screen.getByLabelText('Remove photo 2 of 2'));
    await waitFor(() => expect(puts(PHOTOS_PATH)).toHaveLength(1));
    expect(puts(PHOTOS_PATH)[0]?.body).toEqual({ photo_ids: ['photo-held-1'] });
  });

  it('offers the step’s three acts on a held tile', async () => {
    await openThePhotos();

    fireEvent(screen.getByLabelText('Photo 2 of 2'), 'longPress');

    await screen.findByLabelText('Close photo options');
    expect(screen.getByLabelText(REPLACE_ACTION.label)).toBeTruthy();
    expect(screen.getByLabelText(ADD_ANOTHER_ACTION.label)).toBeTruthy();
    expect(screen.getByLabelText(EDIT_ACTION.label)).toBeTruthy();
  });

  it('keeps the row, says why, and offers the row again when the write is refused', async () => {
    let attempts = 0;
    transport.on('PUT', PHOTOS_PATH, (request) => {
      attempts += 1;
      if (attempts === 1) return errorResponse(403, 'forbidden');
      return json<Wire['PhotosResponse']>({
        photo_ids: (request.body as Wire['ChangePhotosRequest']).photo_ids,
      });
    });
    await openThePhotos();

    fireEvent.press(screen.getByLabelText('Photo 2 of 2'));

    // The row keeps what the player did, and the failure is said with the row offered again.
    expect(await screen.findByLabelText(TRY_AGAIN)).toBeTruthy();
    expect(tileLabels()).toEqual(['Photo 1 of 2, profile photo', 'Photo 2 of 2']);

    fireEvent.press(screen.getByLabelText(TRY_AGAIN));

    await waitFor(() => expect(puts(PHOTOS_PATH)).toHaveLength(2));
    expect(puts(PHOTOS_PATH)[1]?.body).toEqual({ photo_ids: ['photo-held-2', 'photo-held-1'] });
    await waitFor(() => expect(screen.queryByLabelText(TRY_AGAIN)).toBeNull());
  });

  it('re-reads the record behind the header card once a write lands', async () => {
    stubPhotosWrite();
    await openThePhotos();
    const readsBefore = transport.requestsTo('GET', OWN_RECORD_PATH).length;

    fireEvent.press(screen.getByLabelText('Photo 2 of 2'));

    await waitFor(() =>
      expect(transport.requestsTo('GET', OWN_RECORD_PATH).length).toBeGreaterThan(readsBefore),
    );
  });
});

// ---------------------------------------------------------------------------
// Tags
// ---------------------------------------------------------------------------

describe('Tags', () => {
  const HELD_TAGS = PROFILE_SURFACE_SERVED.social_tags;
  const HELD_LINE = tagsLine(HELD_TAGS, MAXIMUM_TAGS);

  const lit = () =>
    screen
      .getAllByRole('button')
      .filter((chip) => chip.props.accessibilityState?.selected === true)
      .map((chip) => String(chip.props.accessibilityLabel));

  async function openTheTags() {
    await onYou();
    fireEvent.press(row(TAGS_TITLE, HELD_LINE));
    await screen.findByRole('header', { name: stepCopy('tags').title });
    await screen.findByLabelText('Plays to win');
  }

  it('opens on the tags the profile holds, under the served bounds, with Saved shut', async () => {
    await openTheTags();

    expect(screen.getByText('On your card · Pick 2 to 6')).toBeTruthy();
    expect(lit()).toEqual([
      'Stays for a drink',
      'Plays to win',
      'Warms up properly',
      'Here to improve',
    ]);
    expect(screen.getByLabelText(SAVED).props.accessibilityState?.disabled).toBe(true);
    expect(fillOf(screen.getByLabelText(SAVED))).toBe(theme.color.mintInk);
    expect(screen.queryByLabelText('Continue')).toBeNull();
  });

  it('refuses a seventh in the step’s words, writes nothing on a press, and the ids on Save — then draws the route’s order', async () => {
    // The route answers in the vocabulary's order, whatever order the picker pressed them in.
    transport.on('PUT', TAGS_PATH, () =>
      json<Wire['SocialTagsResponse']>({
        social_tags: [
          'STAYS_FOR_A_DRINK',
          'PLAYS_TO_WIN',
          'LAUGHS_OFF_MISTAKES',
          'WARMS_UP_PROPERLY',
          'HERE_TO_IMPROVE',
          'HERE_TO_COMPETE',
        ],
      }),
    );
    await openTheTags();

    fireEvent.press(screen.getByLabelText('Here to compete'));
    fireEvent.press(screen.getByLabelText('Laughs off mistakes'));
    expect(screen.getByLabelText(SAVE).props.accessibilityState?.disabled).toBe(false);
    expect(fillOf(screen.getByLabelText(SAVE))).toBe(theme.color.coralInk);
    expect(puts(TAGS_PATH)).toHaveLength(0);

    fireEvent.press(screen.getByLabelText('Shares a lift'));
    expect(await screen.findByText(socialTagCeilingTitle({ minimum: 2, maximum: 6 }))).toBeTruthy();
    expect(lit()).not.toContain('Shares a lift');

    fireEvent.press(screen.getByLabelText(SAVE));

    await waitFor(() => expect(puts(TAGS_PATH)).toHaveLength(1));
    expect(puts(TAGS_PATH)[0]?.body).toEqual({
      social_tags: [...HELD_TAGS, 'HERE_TO_COMPETE', 'LAUGHS_OFF_MISTAKES'],
    });
    expect(await screen.findByLabelText(SAVED)).toBeTruthy();
    expect(fillOf(screen.getByLabelText(SAVED))).toBe(theme.color.mintInk);

    fireEvent.press(screen.getByLabelText('Back'));
    expect(
      await screen.findByLabelText(
        doorRowLabel(
          TAGS_TITLE,
          tagsLine(
            [
              'STAYS_FOR_A_DRINK',
              'PLAYS_TO_WIN',
              'LAUGHS_OFF_MISTAKES',
              'WARMS_UP_PROPERLY',
              'HERE_TO_IMPROVE',
              'HERE_TO_COMPETE',
            ],
            MAXIMUM_TAGS,
          ),
        ),
      ),
    ).toBeTruthy();
  });

  it('shuts Save under the floor with the step’s own words', async () => {
    await openTheTags();

    fireEvent.press(screen.getByLabelText('Stays for a drink'));
    fireEvent.press(screen.getByLabelText('Plays to win'));
    fireEvent.press(screen.getByLabelText('Warms up properly'));

    expect(
      screen.getByLabelText('Pick 1 more tag to save').props.accessibilityState?.disabled,
    ).toBe(true);
    // An ask, shut: not the settled green, which would say the opposite of the words on it.
    expect(fillOf(screen.getByLabelText('Pick 1 more tag to save'))).toBe(theme.color.coralInk);
    expect(puts(TAGS_PATH)).toHaveLength(0);
  });

  it('keeps the draft and says why when the save is refused', async () => {
    transport.on('PUT', TAGS_PATH, () => errorResponse(403, 'forbidden'));
    await openTheTags();

    fireEvent.press(screen.getByLabelText('Here to compete'));
    fireEvent.press(screen.getByLabelText(SAVE));

    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(lit()).toContain('Here to compete');
    expect(screen.getByLabelText(SAVE)).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// Intro
// ---------------------------------------------------------------------------

describe('Intro', () => {
  const HELD_INTRO = PROFILE_SURFACE_SERVED.intro ?? '';
  const box = () => screen.getByLabelText(INTRO_FIELD_LABEL);

  async function openTheIntro() {
    await onYou();
    fireEvent.press(row(INTRO_TITLE, introLine(HELD_INTRO)));
    await screen.findByRole('header', { name: INTRO_TITLE });
    await screen.findByLabelText(INTRO_FIELD_LABEL);
  }

  it('opens on the line the profile holds, with Saved shut and the withdrawal offered', async () => {
    await openTheIntro();

    expect(box().props.value).toBe(HELD_INTRO);
    expect(screen.getByLabelText(SAVED).props.accessibilityState?.disabled).toBe(true);
    expect(fillOf(screen.getByLabelText(SAVED))).toBe(theme.color.mintInk);
    expect(screen.getByLabelText(REMOVE_INTRO)).toBeTruthy();
  });

  it('pre-empts the two shape refusals under the box and shuts Save before a send', async () => {
    await openTheIntro();

    fireEvent.changeText(box(), 'x'.repeat(INTRO_CAP + 1));
    expect(screen.getByText(INTRO_REFUSAL_SENTENCE.too_long)).toBeTruthy();
    expect(screen.getByLabelText(SAVE).props.accessibilityState?.disabled).toBe(true);
    // Shut coral, not green: nothing about a refused line is settled.
    expect(fillOf(screen.getByLabelText(SAVE))).toBe(theme.color.coralInk);

    fireEvent.changeText(box(), 'Two lines\nof this');
    expect(screen.getByText(INTRO_REFUSAL_SENTENCE.multiline)).toBeTruthy();
    expect(screen.getByLabelText(SAVE).props.accessibilityState?.disabled).toBe(true);

    expect(puts(INTRO_PATH)).toHaveLength(0);
  });

  it('draws the server’s refusal under the box, in the step’s sentence, with the line kept', async () => {
    transport.on('PUT', INTRO_PATH, () =>
      json(
        {
          code: 'intro_not_admitted',
          message: 'intro is not one the platform admits',
          trace_id: 'trace-test',
          details: { reason: 'contains_contact' },
        } satisfies Wire['ErrorResponse'],
        400,
      ),
    );
    await openTheIntro();

    fireEvent.changeText(box(), 'WhatsApp me on 600 700 800');
    fireEvent.press(screen.getByLabelText(SAVE));

    expect(await screen.findByText(INTRO_REFUSAL_SENTENCE.contains_contact)).toBeTruthy();
    expect(puts(INTRO_PATH)[0]?.body).toEqual({ intro: 'WhatsApp me on 600 700 800' });
    expect(box().props.value).toBe('WhatsApp me on 600 700 800');
    // The next keystroke clears it: the line it was about is gone.
    fireEvent.changeText(box(), 'Will travel');
    await waitFor(() =>
      expect(screen.queryByText(INTRO_REFUSAL_SENTENCE.contains_contact)).toBeNull(),
    );
  });

  it('saves the trimmed line, and the row’s line follows', async () => {
    transport.on('PUT', INTRO_PATH, () => noContent());
    await openTheIntro();

    fireEvent.changeText(box(), '  Up for doubles most evenings.  ');
    fireEvent.press(screen.getByLabelText(SAVE));

    await waitFor(() => expect(puts(INTRO_PATH)).toHaveLength(1));
    expect(puts(INTRO_PATH)[0]?.body).toEqual({ intro: 'Up for doubles most evenings.' });
    expect(await screen.findByLabelText(SAVED)).toBeTruthy();
    expect(fillOf(screen.getByLabelText(SAVED))).toBe(theme.color.mintInk);

    fireEvent.press(screen.getByLabelText('Back'));
    expect(
      await screen.findByLabelText(
        doorRowLabel(INTRO_TITLE, introLine('Up for doubles most evenings.')),
      ),
    ).toBeTruthy();
  });

  it('withdraws the line with null, empties the box, and the row says none', async () => {
    transport.on('PUT', INTRO_PATH, () => noContent());
    await openTheIntro();

    fireEvent.press(screen.getByLabelText(REMOVE_INTRO));

    await waitFor(() => expect(puts(INTRO_PATH)).toHaveLength(1));
    expect(puts(INTRO_PATH)[0]?.body).toEqual({ intro: null });
    await waitFor(() => expect(box().props.value).toBe(''));
    expect(screen.queryByLabelText(REMOVE_INTRO)).toBeNull();

    fireEvent.press(screen.getByLabelText('Back'));
    expect(await screen.findByLabelText(doorRowLabel(INTRO_TITLE, NO_INTRO_LINE))).toBeTruthy();
  });

  it('shuts Save on a blank box — the way to no intro is the withdrawal', async () => {
    await openTheIntro();

    fireEvent.changeText(box(), '   ');

    expect(screen.getByLabelText(SAVE).props.accessibilityState?.disabled).toBe(true);
    expect(screen.getByLabelText(REMOVE_INTRO)).toBeTruthy();
  });

  it('opens with nothing in the box where no line was written', async () => {
    const { intro: _none, ...noIntro } = PROFILE_SURFACE_SERVED;
    stubProfileSurface(transport, noIntro);
    await onYou();

    fireEvent.press(row(INTRO_TITLE, NO_INTRO_LINE));
    await screen.findByLabelText(INTRO_FIELD_LABEL);

    expect(box().props.value).toBe('');
    expect(screen.queryByLabelText(REMOVE_INTRO)).toBeNull();
  });
});
