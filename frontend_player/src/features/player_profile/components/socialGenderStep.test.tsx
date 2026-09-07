/**
 * The gender step, driven through the real route tree with only the socket faked.
 *
 * The router, the http client, the domain rules, the draft and the screen all run for real,
 * and every assertion is about what a player can see, operate or be told.
 *
 * **Three things here are the record rather than the screen.**
 *
 * The answer about the player is **required and never pre-selected** — `prefer not to say`
 * is a choice somebody makes, not a default given on their behalf, and the continue stays
 * shut until one of the three is pressed.
 *
 * The preference beside it opens at **Anyone**, and that is the opposite decision made for
 * the opposite reason: unconstrained is not a blank to be filled but the value every profile
 * already carries, so a player who never touches that control has answered it at the only
 * setting that takes nothing away from anybody.
 *
 * And narrowing it **says what it costs, at the moment of the press** — including the half
 * nobody would guess, that the excluded side stops being able to reach the player at all.
 * The gate is mutual
 * ([ADR-0096](../../../../../docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)),
 * and learning that from an empty inbox is not acceptable.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';
import { Text } from 'react-native';

import { refreshTokens } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  launchSignedIn,
  resetLocation,
  stubGate as stubGateWith,
  stubLocation,
  stubProfileOptions,
} from '@/test-support/onboardingRouter';
import { fakeLocation } from '@/test-support/platform';
import { installTransport, type Transport, type Wire } from '@/test-support/transport';

import { reachOf } from '../domain/gender';
import { useProfileDraft } from '../store/profileDraft.store';

import { GENDER_SCOPE, PREFER_NOT_TO_SAY_COST, reachNote } from './genderPresentation';

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

let transport: Transport;

const control = (label: string) => screen.getByLabelText(label);
const isSelected = (label: string) => control(label).props.accessibilityState?.selected;
const isDisabled = (label: string) => control(label).props.accessibilityState?.disabled;

/**
 * What the part is holding.
 *
 * Read here for the reason the opt-in suite reads its copy version: **neither value is ever
 * drawn back to the player anywhere in this app**, because no response shape carries a
 * gender out (ADR-0096 §6). There is no on-screen form of *what was recorded* to assert
 * against, and the alternative to reading the draft is to assert nothing.
 */
const held = () => useProfileDraft.getState().draft;

/** A launch by a player the gate owes the second part to, walked as far as step six. */
async function reachTheGenderStep() {
  stubGateWith(transport, { ratings: [RATING], hasPlayerProfile: false });
  stubProfileOptions(transport);
  stubLocation(fakeLocation());

  await launchSignedIn();

  await waitFor(() => expect(screen).toHavePathname('/tags'));
  fireEvent.press(await screen.findByLabelText('Plays to win'));
  fireEvent.press(screen.getByLabelText('Here to improve'));
  fireEvent.press(await screen.findByLabelText('Continue'));

  await waitFor(() => expect(screen).toHavePathname('/photos'));
  fireEvent.press(screen.getByLabelText('Continue'));

  await waitFor(() => expect(screen).toHavePathname('/availability'));
  fireEvent.press(screen.getByLabelText('Wednesday evening'));
  fireEvent.press(screen.getByLabelText('Continue'));

  await waitFor(() => expect(screen).toHavePathname('/location'));
  fireEvent.press(screen.getByLabelText('Continue without matching'));

  await waitFor(() => expect(screen).toHavePathname('/radius'));
  fireEvent.press(await screen.findByLabelText('Continue'));

  await waitFor(() => expect(screen).toHavePathname('/gender'));
  await screen.findByLabelText('Woman');
}

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  useProfileDraft.getState().reset();
});

afterEach(() => {
  transport.restore();
  resetLocation();
  queryClient.clear();
});

describe('what the step opens with', () => {
  it('offers three answers about the player, none of them chosen for them', async () => {
    await reachTheGenderStep();

    for (const label of ['Woman', 'Man', 'Prefer not to say']) {
      expect(isSelected(label)).toBe(false);
    }
    expect(held()?.gender).toBeUndefined();
  });

  it('opens the preference at the widest setting, because that is what a profile holds', async () => {
    // Not a blank to be filled. Unconstrained is the value every player already carries, so
    // there is nothing here for a step to have failed to collect — and the only default the
    // product may give on somebody's behalf is the one that takes nothing from anyone.
    await reachTheGenderStep();

    expect(isSelected('Anyone')).toBe(true);
    expect(isSelected('Women only')).toBe(false);
    expect(held()?.genderPreference).toBe('any');
  });

  it('keeps the continue shut until the player answers about themselves', async () => {
    await reachTheGenderStep();

    expect(isDisabled('Continue')).toBe(true);

    fireEvent.press(control('Man'));

    expect(isDisabled('Continue')).toBeFalsy();
  });

  it('says what both answers are used for above both of them', async () => {
    // A player asked a question about themselves is entitled to know what is done with the
    // answer, and *never shown on your profile* is the part that is least guessable — it is
    // said before the press rather than reassured about after it.
    //
    // It sits at the top rather than between the two controls, which is what makes that
    // true: a player deciding whether to answer at all decides it before pressing anything,
    // and the claim covers the preference below as much as the answer above.
    await reachTheGenderStep();

    expect(screen.getByText(GENDER_SCOPE)).toBeTruthy();
    expect(GENDER_SCOPE).toContain('only to match you with other players');
    expect(GENDER_SCOPE).toContain('never shown on your profile or shared with other players');

    // Above *About you*, which is above the first control — read off the tree rather than
    // asserted about a layout, so a note moved back under the buttons fails here.
    const order = screen
      .UNSAFE_getAllByType(Text)
      .map((node) => String(node.props.children))
      .filter((text) => text === GENDER_SCOPE || text === 'About you');

    expect(order).toEqual([GENDER_SCOPE, 'About you']);
  });

  /** A setting, not a one-off, and it says where to change it. */
  it('says the preference is durable and where it applies', async () => {
    await reachTheGenderStep();

    expect(
      screen.getByText(
        'You can change this later in your preferences. It applies to every search.',
      ),
    ).toBeTruthy();
  });
});

describe('answering about the player', () => {
  it('records the answer and announces it as state rather than leaving it to the fill', async () => {
    await reachTheGenderStep();

    fireEvent.press(control('Woman'));

    expect(held()?.gender).toBe('woman');
    // Colour alone is never the state: *not chosen* and *not a choice* are different things
    // to be told, so all three controls carry the fact.
    expect(isSelected('Woman')).toBe(true);
    expect(isSelected('Man')).toBe(false);
    expect(isSelected('Prefer not to say')).toBe(false);
  });

  it('lets the player change their mind, and the last answer wins', async () => {
    await reachTheGenderStep();

    fireEvent.press(control('Woman'));
    fireEvent.press(control('Man'));

    expect(held()?.gender).toBe('man');
    expect(isSelected('Woman')).toBe(false);
  });

  it('takes prefer not to say as an answer, and says what it costs', async () => {
    // It is a choice and not a blank — it opens the continue exactly as the other two do —
    // and it is the one answer that is not free: it matches an unconstrained search and
    // never a narrowed one. The screen says so, without editorialising about it.
    await reachTheGenderStep();

    expect(screen.queryByText(PREFER_NOT_TO_SAY_COST)).toBeNull();

    fireEvent.press(control('Prefer not to say'));

    expect(held()?.gender).toBe('prefer-not-to-say');
    expect(isDisabled('Continue')).toBeFalsy();
    expect(screen.getByText(PREFER_NOT_TO_SAY_COST)).toBeTruthy();
  });
});

describe('narrowing who the player is matched with', () => {
  it('says nothing about a consequence that is not happening', async () => {
    await reachTheGenderStep();

    expect(screen.queryByText(reachNote(reachOf('women-only')) ?? '')).toBeNull();
    expect(screen.queryByText(reachNote(reachOf('men-only')) ?? '')).toBeNull();
  });

  it('says what narrowing costs at the moment of the press, both directions', async () => {
    // **The sentence ADR-0096 requires.** The visible half — you will not be matched with
    // men — is the half the player asked for. The other half is that men can no longer
    // reach them at all, including men who searched for anybody, and a player who learned
    // that from a quiet inbox would have been told at the one moment it could not help.
    await reachTheGenderStep();

    fireEvent.press(control('Women only'));

    expect(held()?.genderPreference).toBe('women-only');
    expect(screen.getByText(reachNote(reachOf('women-only')) ?? '')).toBeTruthy();
  });

  it('takes the warning away again when the player widens back out', async () => {
    await reachTheGenderStep();

    fireEvent.press(control('Men only'));
    expect(screen.getByText(reachNote(reachOf('men-only')) ?? '')).toBeTruthy();

    fireEvent.press(control('Anyone'));

    expect(held()?.genderPreference).toBe('any');
    expect(screen.queryByText(reachNote(reachOf('men-only')) ?? '')).toBeNull();
  });

  it('does not let a narrowed preference hold the continue shut', async () => {
    // Narrowing is an answer, not a problem to resolve before continuing. What it costs is
    // said; nothing about it is treated as an error.
    await reachTheGenderStep();

    fireEvent.press(control('Woman'));
    fireEvent.press(control('Women only'));

    expect(isDisabled('Continue')).toBeFalsy();
  });
});

describe('the answers the part holds', () => {
  it('are still there after walking back to the step before and returning', async () => {
    await reachTheGenderStep();

    fireEvent.press(control('Man'));
    fireEvent.press(control('Men only'));

    fireEvent.press(control('Back to How far should we look for players?'));
    await waitFor(() => expect(screen).toHavePathname('/radius'));
    fireEvent.press(await screen.findByLabelText('Continue'));
    await waitFor(() => expect(screen).toHavePathname('/gender'));

    expect(isSelected('Man')).toBe(true);
    expect(isSelected('Men only')).toBe(true);
    expect(screen.getByText(reachNote(reachOf('men-only')) ?? '')).toBeTruthy();
  });

  it('reach the server nowhere in the step itself', async () => {
    // The part writes once, at the end. Every answer here is client-held until the commit,
    // so this step makes no request of its own — and neither value ever comes back.
    await reachTheGenderStep();
    const before = transport.requests.length;

    fireEvent.press(control('Woman'));
    fireEvent.press(control('Women only'));

    expect(transport.requests.length).toBe(before);
  });
});
