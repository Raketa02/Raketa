/**
 * **The You tab** — a header card over three titled groups of rows, and *Sign out* at the foot
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §1; [`the-you-screen.md`](../../../../../docs/specs/you/the-you-screen.md) §2).
 *
 * ```
 * header card       the record's header, compact — tapping it opens How others see you
 * PLAYING           Skill passport · Player reliability · What kind of game
 * FINDING PLAYERS   Your week · How far to look · Where you play · Who you play with ·
 *                   Game suggestions
 * ON YOUR CARD      How others see you · Photos · Tags · Intro · Name
 * Sign out
 * ```
 *
 * ## The shell composes, and owns only the tab's own words
 *
 * The title, the eyebrow and the three group titles are the shell's (`youCopy`); **every row
 * from *Skill passport* down is the feature's whose fact it is** — `player_record`'s two
 * read-only facts and the door to the sheet, `player_profile`'s declarations, `auth`'s name —
 * and each row reads its own fact and pushes its own screen. What this file decides is which
 * row sits in which group, and in what order: three groups because the rows answer three
 * questions — what has the platform concluded about me, what does the matcher read when it
 * looks for a game, what does a stranger read about me. The fourth question, the account, is
 * not asked on this tab (§9); *Sign out* stays at the foot as the account panel draws it.
 *
 * ## The switcher chip
 *
 * **The header's right slot is the profile switcher** ([#518](https://github.com/Raketa02/Raketa/issues/518),
 * club 7; ADR-0185 §3 amends ADR-0179 §1's locked header by exactly this element) — the
 * administrator feature's, drawn only for an account that also runs a club's groups. **The route
 * file hands it in** (`headerRight`) rather than this file importing it: the administrator feature
 * reads `auth`, which reads this one, and a feature importing back into that chain is a cycle.
 *
 * ## The one overlay the tab holds
 *
 * *How others see you* is the record sheet on `{ kind: 'me' }`, and two things open it — the
 * header card and the row — so whether it is up is this screen's state and both are handed the
 * same press. The sheet is a sibling of the screen it covers, never a child: `behindOverlay`
 * hides everything inside the element carrying it, and an overlay rendered in there would hide
 * itself along with the screen.
 *
 * ## It is no longer a placeholder, and nothing on it says so
 *
 * The line that named what the tab would be — *your profile, your radius, your week — not
 * built yet* — is gone with the placeholder table it lived in. What replaced the citation is
 * the thing it cited.
 */

import { useState, type ReactNode } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { AccountPanel, NameRow } from '@/features/auth/types';
import {
  GameSuggestionsRow,
  HowFarToLookRow,
  IntroRow,
  PhotosRow,
  TagsRow,
  WhatKindOfGameRow,
  WhereYouPlayRow,
  WhoYouPlayWithRow,
  YourWeekRow,
} from '@/features/player_profile/types';
import {
  HowOthersSeeYouRow,
  OwnRecordSheet,
  PlayerReliabilityRow,
  SkillPassportRow,
  YouHeaderCard,
} from '@/features/player_record/types';
import { Card, behindOverlay, theme } from '@/shared/ui';

import { ShellScreen } from './ShellScreen';
import { YOU_COPY } from './youCopy';

export interface YouScreenProps {
  /**
   * **The header's right slot — the profile switcher's chip**, handed in by the route file, which
   * composes it from the administrator feature: this feature importing that one would close an
   * import cycle through `auth`. Absent, the header has no right slot.
   */
  readonly headerRight?: ReactNode;
}

export function YouScreen({ headerRight }: YouScreenProps) {
  const [reading, setReading] = useState(false);
  const openRecord = () => setReading(true);

  return (
    <>
      <View style={s.root} {...behindOverlay(reading)}>
        <ShellScreen
          title={YOU_COPY.title}
          eyebrow={YOU_COPY.eyebrow}
          {...(headerRight === undefined ? {} : { right: headerRight })}
        >
          <YouHeaderCard onPress={openRecord} />

          <YouGroup title={YOU_COPY.groups.playing}>
            <SkillPassportRow />
            <PlayerReliabilityRow divided />
            <WhatKindOfGameRow divided />
          </YouGroup>

          <YouGroup title={YOU_COPY.groups.findingPlayers}>
            <YourWeekRow />
            <HowFarToLookRow divided />
            <WhereYouPlayRow divided />
            <WhoYouPlayWithRow divided />
            <GameSuggestionsRow divided />
          </YouGroup>

          <YouGroup title={YOU_COPY.groups.onYourCard}>
            <HowOthersSeeYouRow onPress={openRecord} />
            <PhotosRow divided />
            <TagsRow divided />
            <IntroRow divided />
            <NameRow divided />
          </YouGroup>

          <AccountPanel />
        </ShellScreen>
      </View>

      <OwnRecordSheet visible={reading} onClose={() => setReading(false)} />
    </>
  );
}

/**
 * A group: a `flab` title, uppercase, over one `Card` of rows (Part 16, 2026-09-17).
 *
 * The card's vertical padding is a step smaller than a card's own, because the rows carry
 * their own and a card padded as if for prose would put a band of nothing above the first row
 * and below the last.
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
  root: { flex: 1 },
  group: { gap: theme.space.xs, paddingTop: theme.space.xs },
  groupTitle: { ...theme.type.flab, color: theme.color.ink, textTransform: 'uppercase' },
  rows: { paddingVertical: theme.space.xxs },
});
