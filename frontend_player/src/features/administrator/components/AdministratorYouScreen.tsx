/**
 * **The administrator's You tab** — who is here, each official group's settings, *Start playing*
 * and the way out ([#517](https://github.com/Raketa02/Raketa/issues/517), PRD #500 stories
 * 131–133). No mock draws it, so it is the player's You tab's arrangement (ADR-0179 §1) with the
 * administrator's rows in it:
 *
 * ```
 * Marta Nowak                   the account's name — club 8's header, which club 17 moved here
 * GROUP SETTINGS                one row per official group she runs, opening its settings
 * PLAYING                       Start playing — only while the account does not act as a player
 * ─────────────
 * Sign out                      pinned under the page, above the bar
 * ```
 *
 * **The header is the person's name**, club 8's, which PRD #500 moved here from the Groups tab — the
 * one tab about the account. Club 8's *OGRODY 33 · ADMINISTRATOR* over it went at the product
 * owner's ask (#529, 2026-10-02), as the Groups tab's had: the switcher chip beside the name and
 * the area's own bar already say whose profile it is. **The switcher chip is its right slot** ([#518](https://github.com/Raketa02/Raketa/issues/518),
 * club 7), drawn only for an account with a second profile to switch to.
 *
 * **A group's row is the You tab's door row**: a glyph, the group's name, and the one of its settings
 * the Groups tab's read already carries — its sports — so the tab asks nothing of its own. The rows
 * come in the Groups tab's order, newest created first, and before the first group there are none:
 * a card of settings for nothing is nothing.
 *
 * ***Start playing* is offered while the account does not act as a player** (ADR-0185 §4) — an
 * account an Invitation opened, which has never given the Adult attestation. It pushes that step over
 * this tab — inside the area, so *back* is here — and the naming and the player setup follow through
 * the entry gate; afterwards the account holds both profiles, and the row is gone because the
 * account plays.
 *
 * ***Sign out* is the account's**, the player You tab's foot (`AccountPanel`): an account that only
 * administers has no other screen with a way out. **It is pinned under the page**, as on the
 * player's You tab, so it is always at the foot however many groups are listed over it (#529).
 */

import { router } from 'expo-router';
import type { ReactNode } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';

import { AccountPanel, useCurrentUser } from '@/features/auth/types';
import { ReadFailure } from '@/features/groups/types';
import { Card, DoorRow, ScreenHeader, theme, TopSafeArea } from '@/shared/ui';

import { useAdministeredGroups } from '../hooks/useOfficialGroups';

import { ADMINISTRATOR_COPY } from './administratorCopy';
import { settingsRowLine } from './administratorPresentation';
import { groupSettingsRoute, startPlayingRoute } from './administratorRoutes';
import { ProfileChip } from './ProfileChip';

const COPY = ADMINISTRATOR_COPY.you;

export function AdministratorYouScreen({ clubId }: { readonly clubId: string }) {
  const user = useCurrentUser();
  // The area opened on this read, so it is here; *acts as a player* until it says otherwise, so
  // the row never flashes in for an account that plays.
  const plays = user.data?.profiles.actsAsPlayer ?? true;

  return (
    <TopSafeArea style={s.screen}>
      <ScreenHeader
        title={user.data?.name ?? COPY.title}
        right={<ProfileChip worn={{ kind: 'administrator', clubId }} />}
      />
      <ScrollView contentContainerStyle={s.content}>
        <GroupSettingsRows clubId={clubId} />

        {plays ? null : (
          <YouGroup title={COPY.playing}>
            <DoorRow
              glyph="play-circle"
              title={COPY.startPlaying}
              line={COPY.startPlayingLine}
              onPress={() => router.push(startPlayingRoute(clubId))}
            />
          </YouGroup>
        )}
      </ScrollView>

      <View style={s.foot}>
        <AccountPanel />
      </View>
    </TopSafeArea>
  );
}

/** One row per official group, off the Groups tab's read — or why it could not be read. */
function GroupSettingsRows({ clubId }: { readonly clubId: string }) {
  const read = useAdministeredGroups(clubId);
  const groups = read.data?.groups;

  if (groups === undefined) {
    return read.error === null ? null : (
      <YouGroup title={COPY.groups}>
        <ReadFailure error={read.error} onRetry={() => void read.refetch()} />
      </YouGroup>
    );
  }
  if (groups.length === 0) return null;

  return (
    <YouGroup title={COPY.groups}>
      {groups.map((group, index) => {
        const line = settingsRowLine(group);
        return (
          <DoorRow
            key={group.id}
            glyph="sliders"
            title={group.name}
            {...(line === undefined ? {} : { line })}
            divided={index > 0}
            onPress={() => router.push(groupSettingsRoute(clubId, group.id))}
          />
        );
      })}
    </YouGroup>
  );
}

/**
 * A group: a `flab` title, uppercase, over one `Card` of rows — the player You tab's (`shell`'s
 * `YouGroup`, Part 16, 2026-09-17), drawn here for the second tab that has one.
 */
function YouGroup({ title, children }: { readonly title: string; readonly children: ReactNode }) {
  return (
    <View style={s.group}>
      <Text style={s.groupTitle}>{title}</Text>
      <Card style={s.rows}>{children}</Card>
    </View>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  content: {
    paddingHorizontal: theme.size.gutter,
    paddingBottom: theme.space.lg,
    gap: theme.space.sm,
  },
  // The shell's pinned action slot, as the player's You tab draws it (`ShellScreen`).
  foot: {
    paddingHorizontal: theme.size.gutter,
    paddingTop: theme.space.md,
    paddingBottom: theme.space.md,
  },
  group: { gap: theme.space.xs, paddingTop: theme.space.xs },
  groupTitle: { ...theme.type.flab, color: theme.color.ink, textTransform: 'uppercase' },
  rows: { paddingVertical: theme.space.xxs },
});
