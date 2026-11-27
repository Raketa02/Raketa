/**
 * **The club's administrator routes, faked** — the fixtures and the small server the administrator
 * area's router suites walk against ([#516](https://github.com/Raketa02/Raketa/issues/516),
 * [#517](https://github.com/Raketa02/Raketa/issues/517); PRD #500, club mocks 8–11 and 17–20).
 *
 * Ogrody 33, the people who ask to join its groups, two official groups as club 17–19 draw them,
 * and `club()`: the rules the routes document and nothing more — the groups this Administrator
 * runs, newest created first; a create and a settings save checked field by field in the form's
 * order; a switch to Anyone admitting everybody waiting; an approval making the person a player at
 * once; a decline removing the request; and, once the club has removed them,
 * `not_an_administrator` on every route. So a create, a save, an approval or a removal changes
 * what the next read says, as it would.
 *
 * Not app code — nothing under `src/` imports this, so Metro never bundles it.
 */

import {
  errorResponse,
  json,
  noContent,
  type RecordedRequest,
  type Transport,
  type Wire,
} from './transport';

/** The four sports in the registry's order — the order a group's sports are always served in. */
const REGISTRY: readonly Wire['Sport'][] = ['PADEL', 'TENNIS', 'SQUASH', 'BADMINTON'];

export const CLUB_ID = 'c0000000-0000-4000-8000-000000000033';
export const CLUB = {
  id: CLUB_ID,
  name: 'Ogrody 33',
  sports: ['PADEL', 'TENNIS', 'SQUASH'],
} as const;
export const CLUB_PATH = `/api/v1/administrator/clubs/${CLUB_ID}`;
export const GROUPS_PATH = `${CLUB_PATH}/groups`;

/** Where one official group's settings are saved. */
export const settingsPath = (groupId: string) => `${GROUPS_PATH}/${groupId}/settings`;

/** Marta runs Ogrody 33's WhatsApp groups and has never played on Rakieta. */
export const ADMINISTRATOR_ONLY: Wire['AccountProfilesSchema'] = {
  acts_as_player: false,
  administers: [{ club_id: CLUB_ID, club_name: CLUB.name }],
  pending_invitations: [],
  handovers: [],
};

export interface Person {
  readonly id: string;
  readonly name: string;
  readonly levels: Readonly<Partial<Record<Wire['Sport'], number>>>;
}

export function person(n: number, name: string, levels: Person['levels'] = {}): Person {
  return { id: `e0000000-0000-4000-8000-${String(n).padStart(12, '0')}`, name, levels };
}

export const MICHAL = person(1, 'Michał Rogalski', { PADEL: 2.44, TENNIS: 2.6 });
export const TOMEK = person(2, 'Tomek Kowal', { PADEL: 2.71, TENNIS: 3.1, SQUASH: 2.3 });
export const ANIA = person(3, 'Ania Kowalczyk', { PADEL: 2.68 });
export const STAS = person(4, 'Staś Wójcik', { PADEL: 2.5 });
export const FILIP = person(5, 'Filip Nowak', { TENNIS: 3.0 });
export const BARTEK = person(6, 'bartek.l', { PADEL: 2.9 });
export const KUBA = person(7, 'Kuba Wróbel', { PADEL: 2.8 });

export const EVERYBODY = [MICHAL, TOMEK, ANIA, STAS, FILIP, BARTEK, KUBA];

/** "Now", for *this week* — the router's fake clock is set to it before every walk. */
export const NOW = '2026-09-26T12:00:00Z';

export interface Stay {
  readonly who: Person;
  readonly joinedAt: string;
}

export interface GroupSetup {
  readonly id: string;
  readonly name: string;
  readonly letters: string;
  readonly colour?: number;
  readonly sports?: readonly Wire['Sport'][];
  readonly policy?: Wire['JoinPolicy'];
  readonly size?: number;
  /** Newest joined first, as the server serves them. */
  readonly players?: readonly Stay[];
  /** In the order they asked. */
  readonly requests?: readonly Person[];
}

export const O3_CLUB_ID = 'a0000000-0000-4000-8000-000000000001';
export const OPEN_PLAY_ID = 'a0000000-0000-4000-8000-000000000002';
/** The id the fake server gives the one group a walk creates. */
export const CREATED_ID = 'a0000000-0000-4000-8000-000000000100';
export const LINK_OF: Readonly<Record<string, string>> = {
  [O3_CLUB_ID]: 'https://rakieta.app/join/K7PQ2MXA',
  [OPEN_PLAY_ID]: 'https://rakieta.app/join/R4TW9ZHB',
  [CREATED_ID]: 'https://rakieta.app/join/G4H3JK2M',
};

/** *Ogrody 33 Club* as club 17 and 18 draw it: players, and Michał waiting. */
export const O3_CLUB_GROUP: GroupSetup = {
  id: O3_CLUB_ID,
  name: 'Ogrody 33 Club',
  letters: 'O3',
  colour: 1,
  sports: ['PADEL', 'TENNIS', 'SQUASH'],
  policy: 'PEOPLE_I_APPROVE',
  size: 48,
  players: [
    { who: ANIA, joinedAt: '2026-09-07T18:00:00Z' },
    { who: STAS, joinedAt: '2026-09-07T10:00:00Z' },
    { who: FILIP, joinedAt: '2026-08-31T10:00:00Z' },
  ],
  requests: [MICHAL],
};

/** *Ogrody open play* (club 19): nobody waiting. */
export const OPEN_PLAY_GROUP: GroupSetup = {
  id: OPEN_PLAY_ID,
  name: 'Ogrody open play',
  letters: 'Oo',
  colour: 2,
  sports: ['PADEL', 'TENNIS'],
  policy: 'ANYONE',
  size: 30,
  players: [
    { who: MICHAL, joinedAt: '2026-09-24T09:00:00Z' },
    { who: TOMEK, joinedAt: '2026-08-31T10:00:00Z' },
  ],
};

export function rating(sport: Wire['Sport']): Wire['RatingResponse'] {
  return {
    sport,
    mu: 2.71,
    sigma: 0.62,
    confidence: 28,
    range: { low: 2.1, high: 3.3 },
    band: { name: 'Established', lower: 2.7, upper: 3.8 },
    status: 'initial_estimate',
    engine_version: 'racketskill-v3',
    updated_at: '2026-08-14T09:00:00Z',
  };
}

export function refusal(code: string, field: string): Response {
  return json<Wire['ErrorResponse']>(
    { code, message: 'test failure', trace_id: 'trace-test', details: { field } },
    400,
  );
}

/**
 * **The club's server, faked** — the rules the routes document and nothing more: the groups the
 * administrator runs, newest created first; a create and a settings save checked field by field in
 * the form's order; a save switching to Anyone admitting everybody waiting, and saying who; an
 * approval making the person a player at once; a decline removing the request; and, once the club
 * has removed them, `not_an_administrator` on every route.
 */
export function club(setups: readonly GroupSetup[] = []) {
  const state = {
    removed: false,
    groups: setups.map((setup) => ({
      id: setup.id,
      name: setup.name,
      letters: setup.letters,
      colour: setup.colour ?? 0,
      sports: [...(setup.sports ?? ['PADEL'])],
      policy: setup.policy ?? 'ANYONE',
      size: setup.size ?? 48,
      players: [...(setup.players ?? [])],
      requests: [...(setup.requests ?? [])],
    })),
  };
  type Held = (typeof state.groups)[number];

  const card = (group: Held): Wire['AdministeredGroupCardSchema'] => ({
    id: group.id,
    kind: 'OFFICIAL',
    name: group.name,
    monogram: { letters: group.letters, colour: group.colour },
    sports: group.sports,
    member_count: group.players.length,
    waiting_count: group.requests.length,
    home_club: { id: CLUB_ID, name: CLUB.name },
  });

  const page = (group: Held): Wire['AdministeredGroupResponse'] => ({
    id: group.id,
    kind: 'OFFICIAL',
    name: group.name,
    monogram: { letters: group.letters, colour: group.colour },
    sports: group.sports,
    member_count: group.players.length,
    home_club: { ...CLUB, sports: [...CLUB.sports] },
    link: LINK_OF[group.id] ?? 'https://rakieta.app/join/UNKNOWN0',
    join_policy: group.policy,
    whatsapp_size: group.size,
    players: group.players.map(({ who, joinedAt }) => ({
      player_id: who.id,
      nickname: who.name,
      joined_at: joinedAt,
    })),
    requests: group.requests.map((who) => ({
      player_id: who.id,
      nickname: who.name,
      levels: REGISTRY.flatMap((sport) => {
        const level = who.levels[sport];
        return level === undefined ? [] : [{ sport, level }];
      }),
    })),
  });

  const removed = () => errorResponse(403, 'not_an_administrator');
  const find = (id: string) => state.groups.find((group) => group.id === id);

  /**
   * The four fields checked in the form's order, as both routes check them — the name trimmed and
   * collapsed, and the sports only the club's, in the registry's order however they were ticked.
   */
  function checked(
    body: Wire['OfficialGroupSettingsRequest'],
  ): { readonly refused: Response } | { readonly name: string; readonly sports: Wire['Sport'][] } {
    const name = body.name.trim().replace(/\s+/g, ' ');
    if (name.length < 1 || name.length > 40)
      return { refused: refusal('group_name_invalid', 'name') };
    if (
      !Number.isInteger(body.whatsapp_size) ||
      body.whatsapp_size < 2 ||
      body.whatsapp_size > 1024
    ) {
      return { refused: refusal('whatsapp_size_invalid', 'whatsapp_size') };
    }
    if (body.sports.length === 0) return { refused: refusal('group_sports_required', 'sports') };
    const offered: readonly Wire['Sport'][] = CLUB.sports;
    if (body.sports.some((sport) => !offered.includes(sport))) {
      return { refused: refusal('sport_not_offered_by_club', 'sports') };
    }
    return { name, sports: REGISTRY.filter((sport) => body.sports.includes(sport)) };
  }

  function create(body: Wire['CreateOfficialGroupRequest']): Response {
    const form = checked(body);
    if ('refused' in form) return form.refused;
    const group: Held = {
      id: CREATED_ID,
      name: form.name,
      letters: 'O3',
      colour: 4,
      sports: form.sports,
      policy: body.join_policy,
      size: body.whatsapp_size,
      players: [],
      requests: [],
    };
    state.groups.unshift(group);
    return json(page(group), 201);
  }

  /**
   * **Save the settings** — all four together or none; a switch to Anyone admits everybody waiting
   * at once, in the order they asked, and says who.
   */
  function save(group: Held, body: Wire['OfficialGroupSettingsRequest']): Response {
    const form = checked(body);
    if ('refused' in form) return form.refused;
    const admitted = body.join_policy === 'ANYONE' ? group.requests : [];
    group.name = form.name;
    group.policy = body.join_policy;
    group.size = body.whatsapp_size;
    group.sports = form.sports;
    group.requests = body.join_policy === 'ANYONE' ? [] : group.requests;
    group.players.unshift(...admitted.map((who) => ({ who, joinedAt: NOW })));
    return json<Wire['SavedSettingsResponse']>({
      group: page(group),
      admitted: admitted.map((who) => ({ player_id: who.id, nickname: who.name })),
    });
  }

  return {
    state,
    /** The club removes the administrator, from its website. */
    remove() {
      state.removed = true;
    },
    /** Somebody taps the link in WhatsApp and asks to join. */
    ask(groupId: string, who: Person) {
      find(groupId)?.requests.push(who);
    },
    install(transport: Transport) {
      transport.on('GET', GROUPS_PATH, () =>
        state.removed
          ? removed()
          : json<Wire['AdministeredGroupsResponse']>({
              club: { ...CLUB, sports: [...CLUB.sports] },
              groups: state.groups.map(card),
            }),
      );
      transport.on('POST', GROUPS_PATH, (request) =>
        state.removed ? removed() : create(request.body as Wire['CreateOfficialGroupRequest']),
      );
      for (const id of [O3_CLUB_ID, OPEN_PLAY_ID, CREATED_ID]) {
        // Every route on one group asks the same two things first: still an Administrator, and a
        // group of theirs.
        const onGroup =
          (answer: (group: Held, request: RecordedRequest) => Response) =>
          (request: RecordedRequest) => {
            if (state.removed) return removed();
            const group = find(id);
            return group === undefined
              ? errorResponse(404, 'group_not_found')
              : answer(group, request);
          };

        transport.on(
          'GET',
          `${GROUPS_PATH}/${id}`,
          onGroup((group) => json(page(group))),
        );
        transport.on(
          'PUT',
          settingsPath(id),
          onGroup((group, request) =>
            save(group, request.body as Wire['OfficialGroupSettingsRequest']),
          ),
        );
        for (const who of EVERYBODY) {
          const requestPath = `${GROUPS_PATH}/${id}/requests/${who.id}`;
          transport.on(
            'POST',
            `${requestPath}/approve`,
            onGroup((group) => {
              group.requests = group.requests.filter((asking) => asking.id !== who.id);
              group.players.unshift({ who, joinedAt: NOW });
              return noContent();
            }),
          );
          transport.on(
            'POST',
            `${requestPath}/decline`,
            onGroup((group) => {
              group.requests = group.requests.filter((asking) => asking.id !== who.id);
              return noContent();
            }),
          );
        }
      }
    },
  };
}
