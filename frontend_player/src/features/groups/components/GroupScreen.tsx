/**
 * **A group's page** — its header with the sport filter, and three tabs, Games, Fill in and
 * Friends (play 14–17, 39–55; #512, #513; Q125), each drawn for a sport. **The header is the door
 * to Info** (`GroupHeader`), the group's own screen since Q125.
 *
 * Reached from a card on the Groups list, and **replacing** New group once a group is created, so
 * *back* from here is the list either way. A group created a moment ago is drawn at once — the
 * create's answer seeded its read — with *Group created* over it.
 *
 * **It always opens on Games** (story 51) — which tab it was on is not kept (ADR-0188 §5) — and
 * **on the sport last picked anywhere in Play**, which is (`useGroupSport`). Games, Fill in and
 * Friends are all drawn for that sport, and the pill in the header changes it for every one of
 * them at once.
 *
 * **The filter's bar floats over the header and the page under it** — `SportFilterPage`'s, which
 * Members shares — so while it is open, a tap on the tile is the bar's rather than Info's. On an
 * official group it lists only the sports the group declares (#519); a member rated in none of them
 * gets `AddSportCard` on all three tabs, and the header still opens Info, where the way out is — it
 * is not a sport's.
 *
 * **The header opens Info** (Q125): the tile, the name with the official mark and *N members · Home
 * club* are one button, and the back arrow and the pill keep their own taps. Info is pushed over the
 * page, so the page — and the tab it is on — is still here when the player comes back. **The Owner's
 * count of waiting requests is on the tile's corner** (#529), the Info tab's until Q125, from every
 * tab and spoken with the header — so an Owner on Games knows somebody is asking without opening
 * Info. Nobody else's page reads the requests, so nobody else's tile carries a count.
 *
 * **The Games tab counts the cards where somebody is already In with you** (#553, the screens A1,
 * mock 1's *Games 4*): the same badge, off the deck's own read — the one the tab draws, for the
 * sport the page is on and the kind its switch stands on, so the two never disagree and the count
 * costs no second request. **The *Fill in* tab counts its *Seats to fill*** (#557, mock 11's *Fill
 * in 1*) — the rescue board's own badge, read for the page's sport.
 *
 * **Fill in is `proposals`' board** (#557): *Seats to fill* and *You're In*, and — with neither — the
 * starting card a group has always drawn there (`FillInTab`), handed in as the Games tab hands in
 * its own. *+ Post a game* floats over the page's corner and opens *Post a game* (#558).
 *
 * **Which tab it is on is the page's store** (`groupTab.store`, #558) rather than its state, because
 * *Post a game* turns it to Fill in from over the page, so every way back lands on *You're In*; the
 * entry, and the post's draft with it, go when the page does. A screen pushed over the page — Info,
 * a game's details — leaves it where it was, so back is the tab the player left.
 *
 * **Games lays itself out** (#553): the deck fills the page between the switch and its three
 * buttons, so it is drawn outside the page's scroller, and scrolls itself in the states that are
 * not a deck — the question, the starting card.
 *
 * **A player rated in nothing meets one door** (#730, ADR-0200 §2): in a player group, Games, Fill
 * in and Friends each draw onboarding's `LevelDoor` in place of their content — *Get your level*,
 * or *Carry on with your padel questions* with a run left halfway — and the pass it begins returns
 * to the tab it stood on. No sport pill is drawn until she holds a rating. **On Fill in, *+ Post a
 * game* still floats over the door** (the screens A3), and *Post a game* draws the same door.
 *
 * **The chip ends with *+ Another sport*** while a sport is left to offer (#731, ADR-0200 §4): the
 * picker over the sports she is unrated in — an official group's own, or any — for a pass that
 * returns to the tab the page is on.
 *
 * **A rating pass begun on the page comes back to it** (#729, ADR-0200 §3, §5): the route hands in
 * the tab it began on and the sport it rated last, and the page opens on that tab, standing on that
 * sport — the notice's posture: the page stands on it until the player picks another, never saved
 * as a pick. Its official card hands the tab it is on to the pass it begins.
 *
 * **A notice opens the deck at a card** (#559; the screens A9: *the deck opens with the card on top
 * for You complete it and Challenges*). The route hands in the card's sport, kind and id: the page
 * stands on that sport until the player picks another — never saved as a pick — the switch moves
 * to the card's kind, the page is on Games, and the deck draws the card first while it is dealt.
 *
 * **Games and Fill in pull** — the group, for the header and the starting cards, and every read
 * `proposals` draws the two tabs from (`useRereadGroupGames`): the decks, Fill in, *You're In*'s
 * yeses and their games. One control and one spinner for the page; Fill in's is the page's
 * scroller's, and Games', which lays itself out, is handed to the deck, which puts it on whichever
 * scroller it is in. Friends keeps none. **The page does not re-read on the way back** — it did for
 * Info alone, which re-reads itself now (Q125); the three tabs are drawn for a sport and read their
 * own rows.
 *
 * **Every state has its drawing.** While the read is on its way the header has only its way back.
 * `group_not_found` is one sentence, because the server gives the same answer for *no such group*
 * and *not one of yours* and both have one remedy; any other failure says why and offers the retry.
 * The tabs wait for the sport as well as the group: the phone is read before anything is drawn for
 * a sport, so nothing is drawn for one and then redrawn for another (ADR-0188 §4).
 */

import { router } from 'expo-router';
import { useEffect } from 'react';
import { RefreshControl, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { LevelDoor, fromAGroup } from '@/features/onboarding/types';
import {
  FillInBoard,
  forgetPostDraft,
  useFillInBadge,
  useGamesBadge,
  useRereadGroupGames,
} from '@/features/proposals/types';
import { codeMessage } from '@/shared/errors';
import { Segment, theme, type SegmentOption } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { Group } from '../domain/group';
import { GROUP_TABS, OPENING_TAB, type GroupTab } from '../domain/groupPage';
import type { DeckArrival, ReturningPass } from '../schemas/groupRouteParams';
import { useGroup, useGroupReread } from '../hooks/useGroups';
import { usePull } from '../hooks/usePull';
import { useGameIntent } from '../store/gameIntent.store';
import { useGroupTab } from '../store/groupTab.store';

import { AddSportCard } from './AddSportCard';
import { FillInTab, PostAGame } from './FillInTab';
import { FriendsTab } from './FriendsTab';
import { GamesTab } from './GamesTab';
import { GroupHeader } from './GroupHeader';
import { anotherSportRoute, groupInfoRoute } from './groupRoutes';
import { GROUPS_COPY } from './groupsCopy';
import { fillInTabLabel, gamesTabLabel } from './groupsPresentation';
import { ReadFailure } from './ReadFailure';
import { SportFilterPage } from './SportFilterPage';

const COPY = GROUPS_COPY.group;

/** The three tabs' words — read at load, so from the import-free copy module (`groupsCopy.ts`). */
const TABS: readonly SegmentOption<GroupTab>[] = GROUP_TABS.map((key) => ({
  key,
  label: GROUPS_COPY.group.tabs[key],
}));

interface GroupTabsProps {
  readonly groupId: string;
  readonly selected: GroupTab;
  readonly onSelect: (tab: GroupTab) => void;
}

/** The tab bar — with Games' and Fill in's counts once there is a sport to read them for. */
function GroupTabs({ sport, ...props }: GroupTabsProps & { readonly sport: Sport | undefined }) {
  return sport === undefined ? (
    <Segment options={TABS} selected={props.selected} onSelect={props.onSelect} style={s.tabs} />
  ) : (
    <TabsWithCounts {...props} sport={sport} />
  );
}

function TabsWithCounts({
  groupId,
  selected,
  onSelect,
  sport,
}: GroupTabsProps & { readonly sport: Sport }) {
  const chosen = useGameIntent((state) => state.intent);
  const games = useGamesBadge(groupId, sport, chosen);
  const seats = useFillInBadge(groupId, sport);
  const counted = TABS.map((option) => {
    if (option.key === 'games' && games > 0) {
      return { ...option, badge: games, accessibilityLabel: gamesTabLabel(games) };
    }
    if (option.key === 'fillIn' && seats > 0) {
      return { ...option, badge: seats, accessibilityLabel: fillInTabLabel(seats) };
    }
    return option;
  });
  return <Segment options={counted} selected={selected} onSelect={onSelect} style={s.tabs} />;
}

export interface GroupScreenProps {
  readonly groupId: string;
  /** The card a notice opened the deck at (#559) — absent for a page the player opened. */
  readonly arrival?: DeckArrival;
  /** The tab and the sport a rating pass begun here returns to (#729) — absent otherwise. */
  readonly returning?: ReturningPass;
}

export function GroupScreen({ groupId, arrival, returning }: GroupScreenProps) {
  const read = useGroup(groupId);
  const group = read.data;

  // A pass returning here opens on the tab it began on, from the first frame — the page that
  // began it forgot its tab as it went, so nothing is drawn for Games and then redrawn.
  const returnTab = returning?.tab;
  const tab = useGroupTab((state) => state.tabs[groupId]) ?? returnTab ?? OPENING_TAB;
  const show = useGroupTab((state) => state.show);
  const setTab = (next: GroupTab) => show(groupId, next);
  const reread = useGroupReread(groupId);
  const rereadGames = useRereadGroupGames(groupId);
  // The group, for the header and the starting cards, and the games drawn on Games and Fill in.
  const { refreshing, pull } = usePull(() =>
    Promise.all([reread(), rereadGames()]).then(() => undefined),
  );
  // The Shell's control, drawn as the Shell draws it.
  const pullControl = (
    <RefreshControl
      refreshing={refreshing}
      onRefresh={pull}
      tintColor={theme.color.muted}
      colors={[theme.color.muted]}
      progressBackgroundColor={theme.color.paper}
    />
  );

  // The sport the page stands on until the player picks another: a notice's card's, or the one a
  // returning pass rated last. Opening is not picking — neither is saved (ADR-0188 §2).
  const openingSport = arrival?.sport ?? returning?.sport;

  // A notice's card: the deck, in the card's kind. Before the deck is drawn — it waits for the sport,
  // which is read off the phone — so it is never read for one kind and then another.
  const card = arrival?.card;
  const kind = arrival?.kind;
  useEffect(() => {
    if (kind === undefined) return;
    show(groupId, 'games');
    useGameIntent.getState().choose(kind);
  }, [card, kind, groupId, show]);

  // And the tab a pass returned to is the page's, held where every screen over the page reads it —
  // so Members' card, pressed from over it, begins a pass that returns to this tab too.
  useEffect(() => {
    if (returnTab !== undefined) show(groupId, returnTab);
  }, [returnTab, groupId, show]);

  // The page's tab and *Post a game*'s draft are kept while the page is up, and go with it — so it
  // opens on Games the next time, and the next post starts from nothing.
  useEffect(
    () => () => {
      useGroupTab.getState().forget(groupId);
      forgetPostDraft(groupId);
    },
    [groupId],
  );

  return (
    <SafeAreaView style={s.screen} edges={['top']}>
      <SportFilterPage
        {...(group?.declaredSports === undefined ? {} : { declaredSports: group.declaredSports })}
        {...(openingSport === undefined ? {} : { opening: openingSport })}
        onAnother={(offer) => router.replace(anotherSportRoute(groupId, tab, offer))}
        header={(pill, cover) => (
          <GroupHeader
            groupId={groupId}
            group={group}
            backLabel={COPY.back}
            pill={pill}
            cover={cover}
            onOpen={() => router.push(groupInfoRoute(groupId))}
          />
        )}
      >
        {(sport, toAdd, needsALevel) => {
          // The sport the three sport tabs are drawn for — none while the reader must add one.
          const playing = toAdd.length === 0 ? sport : undefined;
          return group === undefined ? (
            read.error === null ? null : (
              <View style={s.body}>
                <ReadFailure
                  error={read.error}
                  message={codeMessage(COPY.refused, read.error)}
                  onRetry={() => void read.refetch()}
                />
              </View>
            )
          ) : (
            <>
              <GroupTabs groupId={groupId} sport={playing} selected={tab} onSelect={setTab} />
              {tab === 'games' && playing !== undefined ? (
                // The deck lays itself out — see the module note.
                <View style={s.fill}>
                  <GamesTab
                    group={group}
                    sport={playing}
                    refreshControl={pullControl}
                    {...(card === undefined ? {} : { onTop: card })}
                  />
                </View>
              ) : (
                <ScrollView
                  testID="group-page-body"
                  contentContainerStyle={s.body}
                  refreshControl={tab === 'friends' ? undefined : pullControl}
                >
                  {toAdd.length > 0 ? (
                    <AddSportCard sports={toAdd} groupId={groupId} tab={tab} />
                  ) : needsALevel ? (
                    <LevelDoor from={fromAGroup(groupId, tab)} />
                  ) : sport === undefined ? null : (
                    <TabBody tab={tab} group={group} sport={sport} />
                  )}
                </ScrollView>
              )}
              {tab === 'fillIn' && toAdd.length === 0 ? (
                <View style={s.postAGame}>
                  <PostAGame groupId={groupId} />
                </View>
              ) : null}
            </>
          );
        }}
      </SportFilterPage>
    </SafeAreaView>
  );
}

/** The two scrolled tabs drawn for the filter's sport; Games lays itself out. */
function TabBody({
  tab,
  group,
  sport,
}: {
  readonly tab: GroupTab;
  readonly group: Group;
  readonly sport: Sport;
}) {
  switch (tab) {
    case 'games':
      return <GamesTab group={group} sport={sport} />;
    case 'fillIn':
      return <FillInBoard groupId={group.id} sport={sport} empty={<FillInTab group={group} />} />;
    case 'friends':
      return <FriendsTab group={group} sport={sport} />;
  }
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  tabs: { marginHorizontal: theme.size.gutter },
  fill: { flex: 1 },
  body: { padding: theme.size.gutter, gap: theme.space.sm },
  // Over the page's bottom corner, at the gutter (play 46).
  postAGame: { position: 'absolute', right: theme.size.gutter, bottom: theme.size.gutter },
});
