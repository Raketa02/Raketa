/**
 * **The club card's tray reads against the page** — the groups under a club's head sit on a ground
 * that has to be told from the page around the card, and the small grey text on it has to stay
 * readable (#529 D6 walk, 2026-09-28: *the groups part of the card has very similar colour as the
 * background of the screen*).
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react-native';
import { StyleSheet, View } from 'react-native';

import { parse, contrast } from '@/test-support/contrast';
import { theme } from '@/shared/ui';

import type { GroupAtClub, SearchedClub } from '../domain/group';

import { CLUB_CARD_TRAY_TEST_ID, ClubCard } from './ClubCard';
import { GroupAtClubRow } from './GroupAtClubRow';

const TRAY = CLUB_CARD_TRAY_TEST_ID;

const GROUP: GroupAtClub = {
  id: 'a0000000-0000-4000-8000-000000000001',
  kind: 'PLAYER',
  name: 'Ogrody 33 Club',
  monogram: { letters: 'O3', colourKey: 2 },
  sports: ['padel'],
  memberCount: 11,
  joinPolicy: 'PEOPLE_I_APPROVE',
  ownerName: 'Coach Andrzej',
  administratorName: null,
  isAdministrator: false,
  relation: 'NONE',
};

const CLUB: SearchedClub = {
  id: 'c0000000-0000-4000-8000-000000000003',
  name: 'Ogrody 33',
  district: 'Grzegórzki',
  distanceKm: 2.4,
  sports: ['tennis', 'padel'],
  groups: [GROUP],
};

function colourOf(style: unknown, key: 'backgroundColor' | 'color'): string {
  const value = (StyleSheet.flatten(style as never) as Record<string, unknown>)[key];
  if (typeof value !== 'string') throw new Error(`no ${key} on the style`);
  return value;
}

const rgb = (value: string) => parse(value).rgb;

beforeEach(() => {
  render(
    <QueryClientProvider client={new QueryClient()}>
      <View>
        <ClubCard club={CLUB} headLabel="Ogrody 33">
          <GroupAtClubRow group={GROUP} clubName={CLUB.name} variant="join" />
        </ClubCard>
      </View>
    </QueryClientProvider>,
  );
});

describe('the club card’s tray', () => {
  // `paper2` on `paper` was 1,07 — a step the eye does not find at a card's bottom edge.
  it('is a step from the page a reader can see', () => {
    const tray = colourOf(screen.getByTestId(TRAY).props.style, 'backgroundColor');

    expect(contrast(rgb(tray), rgb(theme.color.paper))).toBeGreaterThanOrEqual(1.2);
  });

  // Small text needs 4,5 — `muted` on `paper2` was already 4,49.
  it('keeps the group row’s small grey line readable on it', () => {
    const tray = colourOf(screen.getByTestId(TRAY).props.style, 'backgroundColor');
    const line = colourOf(
      screen.getByText('11 members · Coach Andrzej approves joins').props.style,
      'color',
    );

    expect(contrast(rgb(line), rgb(tray))).toBeGreaterThanOrEqual(4.5);
  });
});
