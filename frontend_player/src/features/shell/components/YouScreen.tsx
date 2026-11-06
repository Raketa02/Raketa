/**
 * **The You tab** — a header card over three titled groups of rows, and *Sign out* at the foot
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §1; [`the-you-screen.md`](../../../../../docs/specs/you/the-you-screen.md) §2).
 *
 * ```
 * header card       the record's header, compact — tapping it opens How others see you
 * PLAYING           Skill passport · Player reliability · What kind of game
 * YOUR GAMES        Your week · Where you play · Who you play with · Friends
 * ON YOUR CARD      How others see you · Photos · Tags · Intro · Nickname
 * ACCOUNT           Games & money · Payments · Notifications · Blocked players
 * ─────────────
 * Sign out          pinned under the page, above the bar
 * ```
 *
 * **The title stands alone**: the eyebrow *Player profile* over it went at the product owner's ask
 * (#529, 2026-10-02) — the bar under the screen already says *You*. **_Sign out_ is pinned**, the
 * shell's `action` slot under the scroller, so it is always at the tab's foot, in the same place
 * however many rows are over it (#529, as a group page's way out stands under its Info).
 *
 * ## The shell composes, and owns only the tab's own words
 *
 * The title and the four group titles are the shell's (`youCopy`); **every row
 * from *Skill passport* down is the feature's whose fact it is** — `player_record`'s two
 * read-only facts and the door to the sheet, `player_profile`'s declarations, `auth`'s nickname —
 * and each row reads its own fact and pushes its own screen. What this file decides is which
 * row sits in which group, and in what order: groups because the rows answer questions — what
 * has the platform concluded about me, what does a proposed game read about when and where I
 * play, what does a stranger read about me, and **how do I pay for a game**. That fourth one was not asked on
 * this tab until money was (ADR-0179 §9, amended by ADR-0189; the screens A7): **ACCOUNT** sits
 * after *On your card* and before *Sign out*, and holds *Games & money* (#554), *Payments*
 * (#552) and *Notifications* (#559), in that order (mock 50), and then *Blocked players* (#587) —
 * the way back from a block when the record is out of reach. *Sign out* stays at the foot as the
 * account panel draws it, pinned under the scroller.
 *
 * **Your games lost two rows** with the old loop's ranking, the only thing that read them:
 * *How far to look* and *Game suggestions* ([#582](https://github.com/Raketa02/Raketa/issues/582)).
 * A setting on this tab is one a proposed game still reads. The group was *Finding players* until
 * ADR-0200 §10 renamed it (#733): nothing on the tab finds players any more.
 *
 * **_Friends_ closes Your games** ([#754](https://github.com/Raketa02/Raketa/issues/754), a call:
 * the friends screens say only *a new row*). The group's rows are who and when a game is with, and a
 * friend is the shortcut to one (ADR-0202) — `friends`' row, its line *3 friends · 1 asked you*,
 * the door to You › Friends.
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

import { AccountPanel, NicknameRow } from '@/features/auth/types';
import { BlockedPlayersRow } from '@/features/blocks/types';
import { FriendsRow } from '@/features/friends/types';
import {
  IntroRow,
  PhotosRow,
  TagsRow,
  WhatKindOfGameRow,
  WhereYouPlayRow,
  WhoYouPlayWithRow,
  YourWeekRow,
} from '@/features/player_profile/types';
import { NotificationsRow } from '@/features/notifications/types';
import { PaymentsRow } from '@/features/payments/types';
import { GamesAndMoneyRow } from '@/features/proposals/types';
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
          {...(headerRight === undefined ? {} : { right: headerRight })}
          action={<AccountPanel />}
        >
          <YouHeaderCard onPress={openRecord} />

          <YouGroup title={YOU_COPY.groups.playing}>
            <SkillPassportRow />
            <PlayerReliabilityRow divided />
            <WhatKindOfGameRow divided />
          </YouGroup>

          <YouGroup title={YOU_COPY.groups.yourGames}>
            <YourWeekRow />
            <WhereYouPlayRow divided />
            <WhoYouPlayWithRow divided />
            <FriendsRow divided />
          </YouGroup>

          <YouGroup title={YOU_COPY.groups.onYourCard}>
            <HowOthersSeeYouRow onPress={openRecord} />
            <PhotosRow divided />
            <TagsRow divided />
            <IntroRow divided />
            <NicknameRow divided />
          </YouGroup>

          <YouGroup title={YOU_COPY.groups.account}>
            <GamesAndMoneyRow />
            <PaymentsRow divided />
            <NotificationsRow divided />
            <BlockedPlayersRow divided />
          </YouGroup>
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
