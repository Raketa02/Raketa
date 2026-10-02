/**
 * **The administrator's You tab, walked** — the name and the club, one row per official group
 * opening its settings, *Start playing* for an account that does not play yet, and *Sign out*
 * ([#517](https://github.com/Raketa02/Raketa/issues/517), PRD #500 stories 131–133).
 *
 * The real route tree with the socket faked; the club's administrator routes are answered by
 * `officialGroupsServer`'s small fake, so a save changes what the next read says, as it would.
 * *Start playing*'s whole walk is `startPlaying.test.tsx`.
 */

import { fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import { clearStoredTokens, getSessionStatus, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { launchSignedIn, stubGate } from '@/test-support/onboardingRouter';
import {
  ADMINISTRATOR_ONLY,
  CLUB_ID,
  club,
  GROUPS_PATH,
  KUBA,
  MICHAL,
  NOW,
  O3_CLUB_GROUP,
  O3_CLUB_ID,
  OPEN_PLAY_GROUP,
  OPEN_PLAY_ID,
  rating,
  refusal,
  settingsPath,
  type GroupSetup,
} from '@/test-support/officialGroupsServer';
import { scrollerOf } from '@/test-support/pinned';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { GROUPS_COPY } from '@/features/groups/types';

import { ADMINISTRATOR_COPY } from './administratorCopy';

const COPY = ADMINISTRATOR_COPY;
const YOU = `/administrator/${CLUB_ID}/you`;

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { name: 'Marta Nowak', nickname: null, profiles: ADMINISTRATOR_ONLY });
  useToastQueue.setState({ queue: [] });
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

const toasts = () => useToastQueue.getState().queue.map((toast) => [toast.message, toast.tone]);

/** Launch as Marta, with the club's server answering, and open the You tab from the bar. */
async function openYou(setups: readonly GroupSetup[] = [O3_CLUB_GROUP, OPEN_PLAY_GROUP]) {
  const server = club(setups);
  server.install(transport);
  await launchSignedIn();
  jest.setSystemTime(new Date(NOW));
  await waitFor(() => expect(screen).toHavePathname(`/administrator/${CLUB_ID}`));

  fireEvent.press(await screen.findByRole('tab', { name: 'You' }));
  await waitFor(() => expect(screen).toHavePathname(YOU));
  expect(await screen.findByRole('header', { name: 'Marta Nowak' })).toBeTruthy();
  return server;
}

// ---------------------------------------------------------------------------

describe('the You tab', () => {
  // #529: the switcher chip and the area's bar already say whose profile it is.
  it('says her name, with nothing over it', async () => {
    await openYou();

    expect(screen.getByRole('header', { name: 'Marta Nowak' })).toBeTruthy();
    expect(screen.queryByText('Ogrody 33 · Administrator')).toBeNull();
    expect(screen.getByRole('tab', { name: 'You', selected: true })).toBeTruthy();
  });

  // #529: in one place however many groups are listed over it, as on the player's You tab.
  it('pins Sign out under the page', async () => {
    await openYou();

    expect(scrollerOf(screen.getByText(COPY.you.groups))).toBeDefined();
    expect(scrollerOf(screen.getByRole('button', { name: 'Sign out' }))).toBeUndefined();
  });

  it('draws one row per official group she runs, each saying what it plays', async () => {
    await openYou();

    expect(screen.getByText(COPY.you.groups)).toBeTruthy();
    const rows = await screen.findAllByRole('button', { name: /^Ogrody (33 Club|open play),/ });
    expect(rows.map((row) => row.props.accessibilityLabel)).toEqual([
      'Ogrody 33 Club, Padel, Tennis, Squash',
      'Ogrody open play, Padel, Tennis',
    ]);
  });

  it('draws no group rows before the first group', async () => {
    await openYou([]);

    expect(screen.queryByText(COPY.you.groups)).toBeNull();
    expect(screen.getByRole('button', { name: /^Start playing/ })).toBeTruthy();
  });

  it('offers Start playing to an account that does not play yet, then Sign out', async () => {
    await openYou();

    expect(
      screen.getByRole('button', {
        name: `${COPY.you.startPlaying}, ${COPY.you.startPlayingLine}`,
      }),
    ).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Sign out' })).toBeTruthy();
  });

  // Both profiles already: the player side exists, and the switcher is how to reach it (#518).
  it('offers no Start playing to an account that already plays', async () => {
    stubGate(transport, {
      name: 'Tomek Kowal',
      ratings: [rating('PADEL')],
      hasPlayerProfile: true,
      profiles: { ...ADMINISTRATOR_ONLY, acts_as_player: true },
    });
    club([O3_CLUB_GROUP]).install(transport);
    await launchSignedIn(YOU);

    expect(await screen.findByRole('header', { name: 'Tomek Kowal' })).toBeTruthy();
    expect(await screen.findByRole('button', { name: /^Ogrody 33 Club,/ })).toBeTruthy();
    expect(screen.queryByRole('button', { name: /^Start playing/ })).toBeNull();
    expect(screen.getByRole('button', { name: 'Sign out' })).toBeTruthy();
  });

  it('signs out, and says nothing about a removal', async () => {
    await openYou();
    transport.on('POST', '/api/v1/auth/logout', () =>
      json<Wire['LogoutResponse']>({ message: 'Logged out successfully' }),
    );

    fireEvent.press(screen.getByRole('button', { name: 'Sign out' }));

    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
    expect(getSessionStatus()).toBe('unauthenticated');
    expect(toasts()).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// A group's settings
// ---------------------------------------------------------------------------

/** Open You, then the group's settings from its row, and wait for the form to hold the group. */
async function openSettings(setup: GroupSetup, setups: readonly GroupSetup[] = [setup]) {
  const server = await openYou(setups);
  fireEvent.press(screen.getByRole('button', { name: new RegExp(`^${setup.name},`) }));
  await waitFor(() => expect(screen).toHavePathname(`${YOU}/settings/${setup.id}`));
  expect(await screen.findByRole('header', { name: COPY.settings.title })).toBeTruthy();
  await waitFor(() => expect(nameField().props.value).toBe(setup.name));
  return server;
}

const nameField = () => screen.getByLabelText('Name');
const sizeField = () => screen.getByLabelText(COPY.newGroup.size);
const saveButton = () => screen.getByRole('button', { name: COPY.settings.save });
const isDisabled = (element: Found) => element.props.accessibilityState?.disabled === true;
/** What a query hands back. */
type Found = ReturnType<typeof screen.getByRole>;

/**
 * **Whether a sentence is said on a field's own card** — the nearest thing around the field that
 * holds the sentence holds no *Save*, so it is the card and not the whole form.
 */
function saidOnItsCard(said: Found, field: Found): boolean {
  const holds = (node: Found, wanted: Found) =>
    node.findAll((inside: Found) => inside === wanted).length > 0;
  let around: Found | null = field;
  while (around !== null && !holds(around, said)) around = around.parent;
  return (
    around !== null &&
    around.findAll((inside: Found) => inside.props.accessibilityLabel === COPY.settings.save)
      .length === 0
  );
}

const sent = (groupId: string) =>
  transport
    .requestsTo('PUT', settingsPath(groupId))
    .map((request) => request.body as Wire['OfficialGroupSettingsRequest']);

describe('a group’s settings', () => {
  it('opens from its row holding what the group says, with Save settled', async () => {
    await openSettings(O3_CLUB_GROUP);

    expect(screen.getByRole('tab', { name: 'You', selected: true })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'People I approve', selected: true })).toBeTruthy();
    expect(sizeField().props.value).toBe('48');
    // The club's sports and only those, each the group declares ticked.
    for (const sport of ['Padel', 'Tennis', 'Squash']) {
      expect(screen.getByRole('button', { name: sport, selected: true })).toBeTruthy();
    }
    expect(screen.queryByRole('button', { name: 'Badminton' })).toBeNull();
    expect(isDisabled(screen.getByRole('button', { name: COPY.settings.saved }))).toBe(true);
  });

  it('renames the group, and the row on You says the new name', async () => {
    await openSettings(O3_CLUB_GROUP);

    fireEvent.changeText(nameField(), 'Ogrody 33  Klub ');
    fireEvent.press(saveButton());

    expect(await screen.findByRole('button', { name: COPY.settings.saved })).toBeTruthy();
    // Trimmed on the phone; the run of spaces is the server's to collapse.
    expect(sent(O3_CLUB_ID)).toEqual([
      {
        name: 'Ogrody 33  Klub',
        join_policy: 'PEOPLE_I_APPROVE',
        whatsapp_size: 48,
        sports: ['PADEL', 'TENNIS', 'SQUASH'],
      },
    ]);
    // The field takes the name as the server recorded it, so *Saved* is true of what is shown.
    expect(nameField().props.value).toBe('Ogrody 33 Klub');

    fireEvent.press(screen.getByRole('button', { name: COPY.settings.back }));
    await waitFor(() => expect(screen).toHavePathname(YOU));
    expect(
      await screen.findByRole('button', { name: 'Ogrody 33 Klub, Padel, Tennis, Squash' }),
    ).toBeTruthy();
  });

  it('changes the group size', async () => {
    await openSettings(O3_CLUB_GROUP);

    fireEvent.changeText(sizeField(), '52');
    fireEvent.press(saveButton());

    expect(await screen.findByRole('button', { name: COPY.settings.saved })).toBeTruthy();
    expect(sent(O3_CLUB_ID).map((body) => body.whatsapp_size)).toEqual([52]);
  });

  it('holds the group size to 2–1024, and says so on the field', async () => {
    await openSettings(O3_CLUB_GROUP);

    for (const typed of ['1', '1025', '4.5']) {
      fireEvent.changeText(sizeField(), typed);
      expect(isDisabled(saveButton())).toBe(true);
      expect(screen.getByText('A whole number from 2 to 1024')).toBeTruthy();
    }
    // Required: an empty field says nothing yet, and cannot be saved.
    fireEvent.changeText(sizeField(), '');
    expect(isDisabled(saveButton())).toBe(true);
    fireEvent.changeText(sizeField(), '1024');
    expect(isDisabled(saveButton())).toBe(false);
    expect(screen.queryByText('A whole number from 2 to 1024')).toBeNull();
  });

  it('changes the sports among the club’s, sent in the registry’s order', async () => {
    await openSettings(OPEN_PLAY_GROUP);

    fireEvent.press(screen.getByRole('button', { name: 'Squash' }));
    fireEvent.press(screen.getByRole('button', { name: 'Padel' }));
    fireEvent.press(saveButton());

    expect(await screen.findByRole('button', { name: COPY.settings.saved })).toBeTruthy();
    expect(sent(OPEN_PLAY_ID).map((body) => body.sports)).toEqual([['TENNIS', 'SQUASH']]);
  });

  it('cannot be saved without a sport or a name', async () => {
    await openSettings(OPEN_PLAY_GROUP);

    fireEvent.press(screen.getByRole('button', { name: 'Padel' }));
    fireEvent.press(screen.getByRole('button', { name: 'Tennis' }));
    expect(isDisabled(saveButton())).toBe(true);

    fireEvent.press(screen.getByRole('button', { name: 'Tennis' }));
    fireEvent.changeText(nameField(), '   ');
    expect(isDisabled(saveButton())).toBe(true);
  });

  it('settles again when the form is put back as the group says', async () => {
    await openSettings(O3_CLUB_GROUP);

    fireEvent.changeText(sizeField(), '52');
    expect(isDisabled(saveButton())).toBe(false);
    fireEvent.changeText(sizeField(), '48');

    expect(isDisabled(screen.getByRole('button', { name: COPY.settings.saved }))).toBe(true);
  });

  // The story, as Marta lives it: 48 → 52, and Anyone, which lets the two waiting in.
  it('switches to Anyone, which admits everybody waiting, and shows who', async () => {
    await openSettings({ ...O3_CLUB_GROUP, requests: [MICHAL, KUBA] });

    fireEvent.changeText(sizeField(), '52');
    fireEvent.press(screen.getByRole('button', { name: 'Anyone' }));
    fireEvent.press(saveButton());

    // #529: asked first, in the words an Owner is asked in — and nothing sent until then.
    const sheet = within(await screen.findByTestId('bottom-sheet'));
    expect(sheet.getByRole('header', { name: 'Let anyone join?' })).toBeTruthy();
    expect(
      sheet.getByText(
        'Selecting Anyone allows anyone to join the group, including players with pending requests.',
      ),
    ).toBeTruthy();
    expect(sent(O3_CLUB_ID)).toEqual([]);
    fireEvent.press(sheet.getByRole('button', { name: GROUPS_COPY.editGroup.save }));

    expect(await screen.findByText('Let in · 2')).toBeTruthy();
    expect(
      screen.queryAllByTestId(/^admitted-/).map((row) => row.props.accessibilityLabel as string),
    ).toEqual(['Michał Rogalski', 'Kuba Wróbel']);
    expect(sent(O3_CLUB_ID)).toEqual([
      {
        name: 'Ogrody 33 Club',
        join_policy: 'ANYONE',
        whatsapp_size: 52,
        sports: ['PADEL', 'TENNIS', 'SQUASH'],
      },
    ]);
  });

  it('saves nothing when the Administrator steps back from Anyone', async () => {
    await openSettings({ ...O3_CLUB_GROUP, requests: [MICHAL] });

    fireEvent.press(screen.getByRole('button', { name: 'Anyone' }));
    fireEvent.press(saveButton());
    fireEvent.press(await screen.findByRole('button', { name: 'Keep People I approve' }));

    await waitFor(() => expect(screen.queryByTestId('bottom-sheet')).toBeNull());
    expect(sent(O3_CLUB_ID)).toEqual([]);
    // The form still holds the choice, unsaved, to change or to save.
    expect(isDisabled(saveButton())).toBe(false);
  });

  it('admits nobody on a save that keeps People I approve, and asks nothing', async () => {
    await openSettings({ ...O3_CLUB_GROUP, requests: [MICHAL] });

    fireEvent.changeText(sizeField(), '52');
    fireEvent.press(saveButton());

    expect(await screen.findByRole('button', { name: COPY.settings.saved })).toBeTruthy();
    expect(screen.queryByTestId('bottom-sheet')).toBeNull();
    expect(screen.queryByText(/^Let in/)).toBeNull();
  });

  it('moves the Groups tab’s count once the switch has let people in', async () => {
    await openSettings({ ...O3_CLUB_GROUP, requests: [MICHAL, KUBA] });

    fireEvent.press(screen.getByRole('button', { name: 'Anyone' }));
    fireEvent.press(saveButton());
    fireEvent.press(
      within(await screen.findByTestId('bottom-sheet')).getByRole('button', {
        name: GROUPS_COPY.editGroup.save,
      }),
    );
    expect(await screen.findByText('Let in · 2')).toBeTruthy();

    fireEvent.press(screen.getByRole('tab', { name: 'Groups' }));

    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: /^Ogrody 33 Club,/ }).props.accessibilityLabel,
      ).toBe('Ogrody 33 Club, 5 members, plays Padel, Tennis, Squash, Ogrody 33'),
    );
  });

  it.each([
    ['group_name_invalid', 'name', 'Give the group a name of up to 40 characters.'],
    ['whatsapp_size_invalid', 'whatsapp_size', 'The group size is a whole number from 2 to 1024.'],
    [
      'sport_not_offered_by_club',
      'sports',
      'The club doesn’t offer one of those sports any more. Pick again.',
    ],
  ])(
    'says a refused %s on its field, and forgets it once the form changes',
    async (code, field, words) => {
      await openSettings(O3_CLUB_GROUP);
      transport.on('PUT', settingsPath(O3_CLUB_ID), () => refusal(code, field));

      fireEvent.changeText(sizeField(), '52');
      fireEvent.press(saveButton());

      const said = await screen.findByText(words);
      expect(said).toBeTruthy();
      // On the field it names — inside that field's card, not under the button.
      const card = {
        name: () => nameField(),
        whatsapp_size: () => sizeField(),
        sports: () => screen.getByRole('button', { name: 'Padel' }),
      }[field]!;
      expect(saidOnItsCard(said, card())).toBe(true);

      fireEvent.changeText(sizeField(), '53');
      expect(screen.queryByText(words)).toBeNull();
    },
  );

  it('says a refusal no field owns under the button', async () => {
    await openSettings(O3_CLUB_GROUP);
    transport.on('PUT', settingsPath(O3_CLUB_ID), () => errorResponse(404, 'group_not_found'));

    fireEvent.changeText(sizeField(), '52');
    fireEvent.press(saveButton());

    expect(await screen.findByText(COPY.settings.refused.group_not_found)).toBeTruthy();
  });

  it('is refused for an administrator the club removed, who is told and signed out', async () => {
    const server = await openSettings(O3_CLUB_GROUP);
    server.remove();

    fireEvent.changeText(sizeField(), '52');
    fireEvent.press(saveButton());

    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
    expect(toasts()).toEqual([
      ['Ogrody 33 removed you as an administrator. You’re signed out.', 'base'],
    ]);
  });

  it('goes back to You, and the You tab lays its own root down', async () => {
    await openSettings(O3_CLUB_GROUP);

    fireEvent.press(screen.getByRole('tab', { name: 'You' }));

    await waitFor(() => expect(screen).toHavePathname(YOU));
    expect(screen.getByRole('tab', { name: 'You', selected: true })).toBeTruthy();
    expect(transport.requestsTo('PUT', settingsPath(O3_CLUB_ID))).toEqual([]);
    expect(transport.requestsTo('GET', GROUPS_PATH).length).toBeGreaterThan(0);
  });
});
