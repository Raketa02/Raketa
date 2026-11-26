/**
 * **A group's page** — its header with the sport filter, and four tabs, **Games · Fill in · You’re in
 * · Friends** (play 14–17, 39–55; #512, #513; Q125; #847, split mock 3), each drawn for a sport. **The header is the door
 * to Info** (`GroupHeader`), the group's own screen since Q125.
 *
 * Reached from a card on the Groups list, and **replacing** New group once a group is created, so
 * *back* from here is the list either way. A group created a moment ago is drawn at once — the
 * create's answer seeded its read — with *Group created* over it.
 *
 * **It always opens on Games** (story 51) — which tab it was on is not kept (ADR-0188 §5) — and
 * **on the sport last picked anywhere in Play**, which is (`useGroupSport`). All four tabs are drawn
 * for that sport, and the pill in the header changes it for every one of them at once.
 *
 * **The filter's bar floats over the header and the page under it** — `SportFilterPage`'s, which
 * Members shares — so while it is open, a tap on the tile is the bar's rather than Info's. On an
 * official group it lists only the sports the group declares (#519); a member rated in none of them
 * gets `AddSportCard` on all four tabs, and the header still opens Info, where the way out is — it
 * is not a sport's.
 *
 * **The header opens Info** (Q125): the tile, the name with the official mark and *N members · Home
 * club* are one button, and the back arrow and the pill keep their own taps. Info is pushed over the
 * page, so the page — and the tab it is on — is still here when the player comes back. **The Owner's
 * count of waiting requests is on the tile's corner** (#529), the Info tab's until Q125, from every
 * tab and spoken with the header — so an Owner on Games knows somebody is asking without opening
 * Info. Nobody else's page reads the requests, so nobody else's tile carries a count.
 *
 * **The Games tab counts the cards where somebody is already In with you, of either kind** (#553,
 * the screens A1, mock 1's *Games 4*; across both kinds since #850): the same badge, off the deck's
 * own read — the one the tab draws, for the sport the page is on and the kind its menu stands on,
 * whose ids are both kinds' — so the count costs no second request and nothing reads the other
 * kind's deck. **The *Fill in* tab counts its rescues** (#557, mock 11's *Fill in 1*) — read for the
 * page's sport — **and *You’re in* its rows** (#847): the reader's live yeses in this group and
 * sport, read as the page opens so the badge has it, never holding up the page or a tab switch
 * (`useYoureInBadge`). **All three count what the player hasn't seen** (#849, #850, ADR-0208): a
 * tab's rows are seen while it is on screen — which is why the page is told whether it is the screen
 * in view (`inView`, read by the route file) and hands that to the deck and the two boards, which
 * mark what they draw; on Games, every card of the kind the deck is on, so the other kind's stay
 * new until the deck moves there, the menu's opening seeing nothing — and **the tab on screen draws no
 * badge** (split override 2).
 *
 * **Fill in and You’re in are `proposals`' boards** (#557, split into a tab each by #847, PRD #844):
 * Fill in holds only the rescues, and says *No seats to fill right now* with none; You’re in holds only
 * the reader's live yeses, and — once neither tab has a row — the starting card a group has always
 * drawn (`YoureInTab`), handed in as the Games tab hands in its own. Neither has a heading. **+ Post a
 * game floats over You’re in's corner, and only there** (split override 1), and opens *Post a game*
 * (#558): the game it makes appears on that tab.
 *
 * **Which tab it is on is the page's store** (`groupTab.store`, #558) rather than its state, because
 * *Post a game* reads it and moves it from over the page (#848): the tab it was opened from is where
 * a back-out returns, and the chevron's name, and **a post — or a join from a cell's sheet — lands
 * on You’re in**, turned under it; the entry, and the post's draft with it, go when the page does. A
 * screen pushed over the page — Info, a game's details — leaves it where it was, so back is the tab
 * the player left.
 *
 * **Games lays itself out** (#553): the deck fills the page between the tabs and its three
 * buttons, so it is drawn outside the page's scroller, and scrolls itself in the states that are
 * not a deck — the question, the starting card. **It stays mounted while another tab is on**, out
 * of sight and not laid out: three cards are some six hundred elements, and drawing them again on
 * every return to Games kept the tab from answering the press. Out of sight it sees nothing (its
 * `inView` is the page's and the tab's), and it reads again on its return if its read has gone
 * stale — what the remount's own read used to bring (`GamesDeck`'s `onScreen`).
 *
 * **Games and Friends each hold a menu** (PRD #859; tab menu mocks 1 to 4, illustrations), where a
 * *Competitive | For fun* row stood under the tabs: selected, the tab draws a chevron and widens for
 * it (`Segment`'s option that owns a menu), and **a press on it opens the menu** — Competitive then
 * For fun, the current one ticked (`TabMenu`). **Friends** (#861) offers it wherever its court is
 * drawn, for the kind of the game being built, hung by the tab's right edge. **Games** (#862) offers it
 * where the switch was live — a sport to play and a deck read that came back with its kinds, of either
 * kind (`useGamesMenu`, off the reads the tab bar and the deck already hold, asking for nothing) — so
 * not while the first read is on its way, after it failed or while the first-time question is up, and
 * still while a newly picked kind is read. Hung by the tab's left edge, its live kinds end in today's
 * count and the kind the intent doesn't want is a door (`kindMenuLines`). **While an intent answer or
 * its finding is out the Games tab is still**: the chevron stays drawn and a press opens nothing (the
 * mutations' own state, off `useGamesMenu`). **The menu is the page's**: its open state is this page's own, it is drawn over the
 * page as the last layer of its tree — never on the modal stage, which would cover the tab bar and the
 * app's bottom bar — and the page measures the tab bar and the tab for it to hang from. A press on
 * the same tab, on a line, on the page around the bar, Android back and the page leaving view close
 * it; **a press on another tab goes there in one tap**, the bar being the one thing its catcher leaves
 * uncovered, and the page closes it on the way. While it is open the body takes no touch at all. **A
 * pick asks the tab it is for**: Friends' court (`FriendsTabHandle`), which keeps the sides it shows
 * as the kind changes and never moves the Games deck's kind (ADR-0202); Games' deck
 * (`GamesDeckHandle`), whose door's panel and write are its own — a door opens the panel, and a live
 * kind, the one it stands on included, is chosen and shuts a panel left open. The menu is open
 * only for the tab and the sport it was opened on, so a notice turning the page to Games or a sport
 * changing under it shuts it, and so does a notice moving the deck's kind; and a menu shut that way is
 * forgotten, never to open again on its own. **To read the Games menu above the body, the page holds
 * the sport filter's state itself** (`useGroupSport`, handed to `SportFilterFrame`).
 *
 * **A player rated in nothing meets one door** (#730, ADR-0200 §2): in a player group, each of the
 * four tabs draws onboarding's `LevelDoor` in place of its content — *Get your level*, or *Carry on
 * with your padel questions* with a run left halfway — and the pass it begins returns to the tab it
 * stood on. No sport pill is drawn until she holds a rating. **On You’re in, *+ Post a game* still
 * floats over the door** (the screens A3), and *Post a game* draws the same door; it is not drawn
 * while an official group's *add a sport* card stands in the tab.
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
 * stands on that sport until the player picks another — never saved as a pick — the deck moves to
 * the card's kind, the page is on Games, and the deck draws the card first while it is dealt.
 *
 * **Games, Fill in and You’re in pull** — the group, for the header and the starting cards, and every
 * read `proposals` draws the three tabs from (`useRereadGroupGames`): the decks, Fill in, the live
 * yeses and their games, whichever tab is pulled. One control and one spinner for the page: Fill
 * in's and You’re in's is the page's scroller's, and Games', which lays itself out, is handed to the
 * deck, which puts it on whichever scroller it is in. Friends keeps none. **The page does not re-read on the way back** — it did for
 * Info alone, which re-reads itself now (Q125); the tabs are drawn for a sport and read their own
 * rows.
 *
 * **The tabs' reads set out with the group's.** The tabs are drawn once the group has been read,
 * and their reads used to set out only then, a round trip behind; while the group is on its way the
 * page asks for the deck of the kind the menu stands on, Fill in and the live yeses for the sport
 * it stands on (`useReadGroupGamesAhead`), and the tabs find them read or on their way.
 *
 * **It shimmers until it is built, then reveals together** ([#875](https://github.com/Raketa02/Raketa/issues/875);
 * PRD #867; the loading shimmer log §10): **two parts, top-down** (`groupPageParts`) — **the header
 * and the tab bar**, which wait for the group and the sport, and **the body of the tab on screen**,
 * which waits for that tab's first read (`proposals`' `useGroupTabRead`). While they wait, on one
 * ground so one band crosses them all, **a monogram circle and a name bar** stand beside the real way
 * back (`GroupHeader`'s `shimmering`), **the tab bar's shape** under them, and the tab's own skeleton
 * — **one deck-card block** on Games, **rows** on Fill in and You’re in, nothing on Friends, which waits
 * on no read here. Everything comes in on one cross-fade once both have finished; **from 2.5 s after
 * the page mounts** (`useRevealParts`' ceiling) the header and the tabs come first and the body keeps
 * its skeleton until its read finishes. **Switching to a tab with nothing read shimmers only its
 * body** — the scroller's `Reveal` is keyed by the tab, and a part shown stays shown. Each `Reveal`
 * keeps its place in the tree from the first frame, Games' and the scroller's alike, so the skeleton
 * standing while the group is read is the one the body's fade carries away. A part revealed with a
 * failure or the offline note shimmers again when its read sets out once more (`partOf`). **What lies
 * over the deck's area reveals Games however far its read has come** (`gamesRead`, told by the deck's
 * `onCovered`): a door picked from the menu once the tab bar is in opens its panel over the deck's own
 * block, and finding after it, rather than under the tab's skeleton, unseen.
 *
 * **Every state has its drawing.** While the read is on its way the header has only its way back,
 * beside the skeleton. **Held for a connection, the page says so** — the amber note in the body,
 * where it once drew nothing at all. `group_not_found` is one sentence, because the server gives the
 * same answer for *no such group* and *not one of yours* and both have one remedy; any other failure
 * says why and offers the retry. **A read that failed once and is retrying keeps the page shimmering**
 * (`groupReadStage`): every part draws from it, so revealing it would show a back arrow over nothing.
 * The tabs wait for the sport as well as the group: the phone is read before anything is drawn for
 * a sport, so nothing is drawn for one and then redrawn for another (ADR-0188 §4).
 */

import { router } from 'expo-router';
import { useCallback, useEffect, useRef, useState, type Ref } from 'react';
import { RefreshControl, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { LevelDoor, fromAGroup } from '@/features/onboarding/types';
import {
  BoardSkeleton,
  DeckSkeleton,
  FillInBoard,
  YoureInBoard,
  forgetPostDraft,
  kindMenuLines,
  useFillInBadge,
  useGamesBadge,
  useGamesMenu,
  useGroupTabRead,
  type GamesDeckHandle,
  useReadGroupGamesAhead,
  useRereadGroupGames,
  useYoureInBadge,
} from '@/features/proposals/types';
import { codeMessage, offlineMessage } from '@/shared/errors';
import {
  Note,
  Reveal,
  Segment,
  SkeletonGround,
  TabMenu,
  theme,
  useRevealParts,
  type MenuFrame,
  type SegmentMenu,
  type SegmentOption,
  type TabMenuLine,
  useTabBarReach,
} from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { Group } from '../domain/group';
import {
  GAME_INTENTS,
  GROUP_TABS,
  OPENING_TAB,
  bodyRead,
  gamesRead,
  groupPageParts,
  groupReadStage,
  type GameIntent,
  type GroupTab,
} from '../domain/groupPage';
import type { DeckArrival, ReturningPass } from '../schemas/groupRouteParams';
import { useGroup, useGroupReread } from '../hooks/useGroups';
import { useGroupSport } from '../hooks/useGroupSport';
import { usePull } from '../hooks/usePull';
import { useFriendsGame } from '../store/friendsGame.store';
import { useGameIntent } from '../store/gameIntent.store';
import { useGroupTab } from '../store/groupTab.store';

import { AddSportCard } from './AddSportCard';
import { FriendsTab, type FriendsTabHandle } from './FriendsTab';
import { GamesTab } from './GamesTab';
import { GroupHeader } from './GroupHeader';
import { GroupTabsSkeleton } from './GroupPageSkeleton';
import { anotherSportRoute, groupInfoRoute } from './groupRoutes';
import { GROUPS_COPY } from './groupsCopy';
import { fillInTabLabel, gamesTabLabel, menuTabLabel, youreInTabLabel } from './groupsPresentation';
import { ReadFailure } from './ReadFailure';
import { SportFilterFrame } from './SportFilterPage';
import { PostAGame, YoureInTab } from './YoureInTab';

const COPY = GROUPS_COPY.group;

/** The four tabs' words — read at load, so from the import-free copy module (`groupsCopy.ts`). */
const TABS: readonly SegmentOption<GroupTab>[] = GROUP_TABS.map((key) => ({
  key,
  label: GROUPS_COPY.group.tabs[key],
}));

/**
 * The Friends tab's menu's lines — the kinds, in their order (#861); no counts, no door. Read at
 * load too, so from the copy module, never `groupsPresentation`'s `KIND_WORDS`: entered from that
 * side of the feature cycle, it is not yet defined when this module runs.
 */
const FRIENDS_LINES: readonly TabMenuLine<GameIntent>[] = GAME_INTENTS.map((kind) => ({
  key: kind,
  label: GROUPS_COPY.group.kinds[kind],
}));

/** The menu open on a tab, for the sport it was opened on — see the module note. */
interface OpenMenu {
  readonly tab: GroupTab;
  readonly sport: Sport;
}

/** Where the menu hangs: the tab bar and the tab in the page, as they stood when it opened. */
interface MenuHung {
  readonly bar: MenuFrame | undefined;
  readonly trigger: MenuFrame | undefined;
}

interface GroupTabsProps {
  readonly groupId: string;
  /** The four tabs, Games and Friends with their menus. */
  readonly options: readonly SegmentOption<GroupTab>[];
  readonly selected: GroupTab;
  readonly onSelect: (tab: GroupTab) => void;
}

/**
 * The tab bar — with Games', Fill in's and You’re in's counts once there is a sport to read them for,
 * and none on the tab selected (#849, #850).
 */
function GroupTabs({ sport, ...props }: GroupTabsProps & { readonly sport: Sport | undefined }) {
  return sport === undefined ? (
    <Segment options={props.options} selected={props.selected} onSelect={props.onSelect} />
  ) : (
    <TabsWithCounts {...props} sport={sport} />
  );
}

function TabsWithCounts({
  groupId,
  options,
  selected,
  onSelect,
  sport,
}: GroupTabsProps & { readonly sport: Sport }) {
  const chosen = useGameIntent((state) => state.intent);
  const games = useGamesBadge(groupId, sport, chosen);
  const seats = useFillInBadge(groupId, sport);
  // The live yeses are read here, as the page opens, so You’re in's badge has them — and the tab,
  // the same read, usually opens already read.
  const yeses = useYoureInBadge(groupId, sport);
  const counted = options.map((option) => {
    // The tab on screen draws no badge (split override 2): what it shows is seen while it is shown —
    // on Games too, where the other kind's new cards show once the player leaves (ADR-0208).
    if (option.key === selected) return option;
    if (option.key === 'games' && games > 0) {
      return { ...option, badge: games, accessibilityLabel: gamesTabLabel(games) };
    }
    if (option.key === 'fillIn' && seats > 0) {
      return { ...option, badge: seats, accessibilityLabel: fillInTabLabel(seats) };
    }
    if (option.key === 'youreIn' && yeses > 0) {
      return { ...option, badge: yeses, accessibilityLabel: youreInTabLabel(yeses) };
    }
    return option;
  });
  return <Segment options={counted} selected={selected} onSelect={onSelect} />;
}

/** A menu the page no longer offers is forgotten, so it never opens again on its own. */
function ForgetsAShutMenu({
  shut,
  forget,
}: {
  readonly shut: boolean;
  readonly forget: () => void;
}) {
  useEffect(() => {
    if (shut) forget();
  }, [shut, forget]);
  return null;
}

export interface GroupScreenProps {
  readonly groupId: string;
  /**
   * Whether the page is the screen in view — nothing pushed over it (`useScreenInView`, read by the
   * route file). What Fill in and You’re in draw is seen only while it is (#849).
   */
  readonly inView: boolean;
  /** The card a notice opened the deck at (#559) — absent for a page the player opened. */
  readonly arrival?: DeckArrival;
  /** The tab and the sport a rating pass begun here returns to (#729) — absent otherwise. */
  readonly returning?: ReturningPass;
}

export function GroupScreen({ groupId, inView, arrival, returning }: GroupScreenProps) {
  // Ends at the bar's reach, its own gap clear of it (10.1, ADR-0210 §3, #881).
  const reach = useTabBarReach();
  const read = useGroup(groupId);
  const group = read.data;

  // The sport the page stands on until the player picks another: a notice's card's, or the one a
  // returning pass rated last. Opening is not picking — neither is saved (ADR-0188 §2).
  const openingSport = arrival?.sport ?? returning?.sport;
  // The filter's state is held here rather than in the frame it draws (`SportFilterFrame`), so the
  // page knows its sport above the body: the Games tab's menu is read for it.
  const filter = useGroupSport(group?.declaredSports, openingSport);

  // A pass returning here opens on the tab it began on, from the first frame — the page that
  // began it forgot its tab as it went, so nothing is drawn for Games and then redrawn.
  const returnTab = returning?.tab;
  const tab = useGroupTab((state) => state.tabs[groupId]) ?? returnTab ?? OPENING_TAB;
  const show = useGroupTab((state) => state.show);
  const setTab = (next: GroupTab) => show(groupId, next);

  // The Games tab's menu (#862), off the deck reads the tab bar and the deck already hold — for the
  // sport the tabs are drawn for, none while the reader must add one.
  const chosenKind = useGameIntent((state) => state.intent);
  const gamesMenu = useGamesMenu(
    groupId,
    filter.toAdd.length === 0 ? filter.sport : undefined,
    chosenKind,
  );

  // **The page's reveal** (#875; see the module note): the header and the tab bar, then the body of
  // the tab on screen — together, or top-down from the ceiling. Games is asked after on its own too,
  // since it stays mounted, out of sight, while another tab is on.
  const playingNow = filter.toAdd.length === 0 ? filter.sport : undefined;
  // What lies over the deck — the door's panel, finding — is drawn, however far its read has come.
  const [deckCovered, setDeckCovered] = useState(false);
  const gamesBody = gamesRead(
    useGroupTabRead(groupId, playingNow, 'games', chosenKind),
    deckCovered,
  );
  const boardRead = useGroupTabRead(
    groupId,
    playingNow,
    tab === 'fillIn' || tab === 'youreIn' ? tab : undefined,
    chosenKind,
  );
  const parts = groupPageParts({
    group: groupReadStage({
      landed: group !== undefined,
      refused: read.error !== null,
      held: read.isPaused,
    }),
    sportAnswered: filter.answered,
    body: bodyRead(
      tab,
      playingNow !== undefined && !filter.needsALevel,
      tab === 'games' ? gamesBody : boardRead,
    ),
  });
  const { shown } = useRevealParts(parts.finished);
  const top = partOf(shown, 1, parts.finished[0], parts.landed[0]);
  const below = partOf(shown, 2, parts.finished[1], parts.landed[1]);
  const games =
    tab === 'games' ? below : partOf(shown, 2, gamesBody !== 'reading', gamesBody === 'landed');

  // The tab's menu — the page's own state (see the module note). The bar and the tab are measured
  // into refs, never state: the tab widens on every switch to Friends and back, and a measure in
  // state would draw the whole page again each time. They are read once, as the menu opens, and
  // kept where it hung while it folds away.
  const [menu, setMenu] = useState<OpenMenu | undefined>(undefined);
  const [hung, setHung] = useState<MenuHung>({ bar: undefined, trigger: undefined });
  const forgetMenu = useCallback(() => setMenu(undefined), []);
  const barFrame = useRef<MenuFrame | undefined>(undefined);
  /** Each tab that owns a menu, where it stands in the bar — Games' and Friends'. */
  const tabFrames = useRef<Partial<Record<GroupTab, MenuFrame>>>({});
  const hangMenu = (from: GroupTab) => {
    const bar = barFrame.current;
    const at = tabFrames.current[from];
    // The tab in the page's coordinates: the bar's place, and the tab's place in the bar.
    setHung({
      bar,
      trigger:
        bar === undefined || at === undefined
          ? undefined
          : { ...at, x: bar.x + at.x, y: bar.y + at.y },
    });
  };
  const friendsKind = useFriendsGame((state) => state.kind);
  const friendsTab = useRef<FriendsTabHandle>(null);
  const gamesDeck = useRef<GamesDeckHandle>(null);
  const reread = useGroupReread(groupId);
  const rereadGames = useRereadGroupGames(groupId);
  // The group, for the header and the starting cards, and the games drawn on Games, Fill in and
  // You’re in.
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

  // A notice's card: the deck, in the card's kind. Before the deck is drawn — it waits for the sport,
  // which is read off the phone — so it is never read for one kind and then another.
  const card = arrival?.card;
  const kind = arrival?.kind;
  // The card whose kind the deck has been moved to. Until it has, the deck sees nothing (#850): on
  // a page whose reads are still cached, the deck is drawn for the kind it stood on a frame before
  // this effect moves it, and would mark cards the player never had on screen. The move shuts a
  // menu left open (#862): the kind it would pick from is not the one it was opened over.
  const [arrivedAt, setArrivedAt] = useState<string | undefined>(undefined);
  const arrived = card === undefined || arrivedAt === card;
  useEffect(() => {
    if (kind === undefined) return;
    show(groupId, 'games');
    useGameIntent.getState().choose(kind);
    setMenu(undefined);
    setArrivedAt(card);
  }, [card, kind, groupId, show]);

  // And the tab a pass returned to is the page's, held where every screen over the page reads it —
  // so Members' card, pressed from over it, begins a pass that returns to this tab too.
  useEffect(() => {
    if (returnTab !== undefined) show(groupId, returnTab);
  }, [returnTab, groupId, show]);

  // The page's tab, *Post a game*'s draft and the Friends court's line-ups are kept while the page
  // is up, and go with it — so it opens on Games the next time, and the next post and the next game
  // with friends start from nothing.
  useEffect(
    () => () => {
      useGroupTab.getState().forget(groupId);
      forgetPostDraft(groupId);
      useFriendsGame.getState().forget(groupId);
    },
    [groupId],
  );

  return (
    <SafeAreaView style={s.screen} edges={['top']}>
      {/* One ground for the page, so one band crosses the header, the tab bar and the body. */}
      <SkeletonGround style={s.fill}>
        <SportFilterFrame
          filter={filter}
          onAnother={(offer) => router.replace(anotherSportRoute(groupId, tab, offer))}
          header={(pill, cover) => (
            <GroupHeader
              groupId={groupId}
              group={group}
              backLabel={COPY.back}
              pill={pill}
              cover={cover}
              onOpen={() => router.push(groupInfoRoute(groupId))}
              shimmering={!top.finished}
            />
          )}
        >
          {(sport, toAdd, needsALevel) => {
            // The sport the four tabs are drawn for — none while the reader must add one.
            const playing = toAdd.length === 0 ? sport : undefined;
            // A tab offers its menu only where there is a sport to play — not on the add-a-sport card,
            // not on the level door: Friends wherever its court is drawn, Games wherever a deck read
            // has come back with its kinds (`useGamesMenu`).
            const court = playing !== undefined && !needsALevel;
            const offers = (key: GroupTab) =>
              court && (key === 'friends' || (key === 'games' && gamesMenu !== undefined));
            const menuOpen =
              menu !== undefined && menu.tab === tab && menu.sport === playing && offers(tab);
            const select = (next: GroupTab) => {
              // A press on the selected tab that offers a menu opens it, or shuts it — on Games, not
              // while an intent answer is on its way or its games are found: the chevron stays, inert.
              if (next === tab && offers(next) && playing !== undefined) {
                if (menuOpen) return setMenu(undefined);
                if (next === 'games' && gamesMenu?.still === true) return;
                hangMenu(next);
                setMenu({ tab: next, sport: playing });
                return;
              }
              setMenu(undefined);
              setTab(next);
            };
            const menuOf = (key: GroupTab): SegmentMenu => ({
              offered: offers(key),
              open: menuOpen && tab === key,
              onFrame: (frame) => {
                tabFrames.current[key] = frame;
              },
            });
            // Selected with its menu offered, a tab says the kind it holds: *Games, Competitive*.
            const heldKind = (key: GroupTab): GameIntent | undefined =>
              key === 'friends' ? friendsKind : key === 'games' ? gamesMenu?.kind : undefined;
            const options = TABS.map((option) => {
              if (option.key !== 'friends' && option.key !== 'games') return option;
              const owned = { ...option, menu: menuOf(option.key) };
              const held = heldKind(option.key);
              return tab === option.key && owned.menu.offered && held !== undefined
                ? { ...owned, accessibilityLabel: menuTabLabel(option.key, held) }
                : owned;
            });
            // **Until the group has been read**, the body is what its read says: the failure with its
            // retry, the offline note — or nothing, its skeleton standing — while the tabs' reads set
            // out beside it (see the module note). At the gutter where it stands outside the scroller,
            // which pads its own content.
            const groupless = (inset: boolean) => {
              const said =
                read.error !== null ? (
                  <ReadFailure
                    error={read.error}
                    message={codeMessage(COPY.refused, read.error)}
                    onRetry={() => void read.refetch()}
                  />
                ) : read.isPaused ? (
                  <Note variant="amber">{offlineMessage('resumes')}</Note>
                ) : null;
              return (
                <>
                  {said !== null && inset ? <View style={s.body}>{said}</View> : said}
                  {read.error === null && playing !== undefined ? (
                    <ReadingAhead groupId={groupId} sport={playing} kind={kind} />
                  ) : null}
                </>
              );
            };
            // Games lays itself out, outside the page's scroller, and stays mounted while another tab
            // is on; until the group is read and the filter has said, it is the body when the page
            // is on Games. The scroller holds every other body. Each keeps its place in the tree from
            // the first frame, so the reveal's one fade carries its skeleton into what replaces it
            // (see the module note).
            const gamesDrawn =
              group === undefined || !filter.answered ? tab === 'games' : playing !== undefined;
            const scrolled = !(tab === 'games' && gamesDrawn);
            return (
              <>
                <View
                  testID="group-tabs"
                  style={s.tabs}
                  onLayout={({ nativeEvent }) => {
                    barFrame.current = nativeEvent.layout;
                  }}
                >
                  <Reveal
                    testID="group-tabs-reveal"
                    sizedBy="skeleton"
                    finished={top.finished}
                    landed={top.landed}
                    skeleton={<GroupTabsSkeleton />}
                  >
                    {group === undefined ? null : (
                      <GroupTabs
                        groupId={groupId}
                        sport={playing}
                        options={options}
                        selected={tab}
                        onSelect={select}
                      />
                    )}
                  </Reveal>
                </View>
                {gamesDrawn ? (
                  // The deck lays itself out — see the module note — and **stays mounted while
                  // another tab is on**, out of sight: coming back to Games shows the cards it
                  // already drew rather than drawing them again (see the module note).
                  <View
                    style={tab === 'games' ? s.fill : s.gone}
                    // Under an open menu the deck takes no touch: a press there only closes it.
                    pointerEvents={menuOpen ? 'none' : 'auto'}
                  >
                    <Reveal
                      testID="group-games-reveal"
                      style={s.fill}
                      finished={games.finished}
                      landed={games.landed}
                      // Drawn only while it is the tab on screen: out of sight, nothing shimmers.
                      skeleton={tab === 'games' ? <DeckSkeleton /> : null}
                    >
                      {group === undefined || playing === undefined ? (
                        groupless(true)
                      ) : (
                        <GamesTab
                          group={group}
                          sport={playing}
                          handle={gamesDeck}
                          onScreen={tab === 'games'}
                          onCovered={setDeckCovered}
                          // A notice's deck sees nothing until it stands on the card's kind, and a
                          // deck out of sight sees nothing at all.
                          inView={inView && arrived && tab === 'games'}
                          refreshControl={pullControl}
                          {...(card === undefined ? {} : { onTop: card })}
                        />
                      )}
                    </Reveal>
                  </View>
                ) : null}
                {scrolled ? (
                  // **The scroller stands alone in a view of its own.** On Android, as a bare
                  // sibling of the tab bar and the deck, the offset it scrolled never reached what
                  // Fabric's `measure` reads, and every press it had scrolled in dropped at a
                  // resting thumb's first move — Friends' *Send game and pay* among them
                  // (architecture.md's platform rules).
                  <View testID="group-page-scroll-frame" style={s.fill}>
                    <ScrollView
                      testID="group-page-body"
                      contentContainerStyle={[s.body, { paddingBottom: reach + theme.size.gutter }]}
                      refreshControl={tab === 'friends' ? undefined : pullControl}
                      // Under an open menu the page takes no touch: a press there only closes it.
                      pointerEvents={menuOpen ? 'none' : 'auto'}
                    >
                      {/* Keyed by the tab: one with nothing read yet shimmers on its own (#875). */}
                      <Reveal
                        key={tab}
                        testID="group-body-reveal"
                        sizedBy="skeleton"
                        finished={below.finished}
                        landed={below.landed}
                        skeleton={tab === 'fillIn' || tab === 'youreIn' ? <BoardSkeleton /> : null}
                      >
                        {group === undefined ? (
                          groupless(false)
                        ) : toAdd.length > 0 ? (
                          <AddSportCard sports={toAdd} groupId={groupId} tab={tab} />
                        ) : needsALevel ? (
                          <LevelDoor from={fromAGroup(groupId, tab)} />
                        ) : sport === undefined ? null : (
                          <TabBody
                            tab={tab}
                            group={group}
                            sport={sport}
                            inView={inView && arrived}
                            friendsTab={friendsTab}
                          />
                        )}
                      </Reveal>
                    </ScrollView>
                  </View>
                ) : null}
                {/* You’re in's alone (split override 1): the game it makes appears on that tab. It
                    comes in with the header and the tab bar (#875), never over a page still
                    shimmering. */}
                {top.landed && tab === 'youreIn' && toAdd.length === 0 ? (
                  <View
                    testID="post-a-game-fab"
                    style={[s.postAGame, { bottom: reach + theme.size.gutter }]}
                  >
                    <PostAGame groupId={groupId} />
                  </View>
                ) : null}
                {/* The tab's menu, over the page, last — see the module note. */}
                {group !== undefined && tab === 'games' && court && gamesMenu !== undefined ? (
                  <TabMenu
                    open={menuOpen}
                    lines={kindMenuLines(gamesMenu.sides)}
                    selected={gamesMenu.ticked}
                    trigger={hung.trigger}
                    bar={hung.bar}
                    align="start"
                    onClose={forgetMenu}
                    // The deck takes the line: a door opens its panel, and a live kind — the one it
                    // stands on too — is chosen and shuts a panel left open.
                    onPick={(picked) => gamesDeck.current?.pick(picked)}
                  />
                ) : null}
                {group !== undefined && tab === 'friends' && court ? (
                  <TabMenu
                    open={menuOpen}
                    lines={FRIENDS_LINES}
                    selected={friendsKind}
                    trigger={hung.trigger}
                    bar={hung.bar}
                    align="end"
                    onClose={forgetMenu}
                    onPick={(kind) => {
                      // The kind it already is just closes the menu.
                      if (kind !== friendsKind) friendsTab.current?.chooseKind(kind);
                    }}
                  />
                ) : null}
                <ForgetsAShutMenu shut={menu !== undefined && !menuOpen} forget={forgetMenu} />
              </>
            );
          }}
        </SportFilterFrame>
      </SkeletonGround>
    </SafeAreaView>
  );
}

/**
 * **A part's two words for its `Reveal`** (#875): shown, and finished — or landed — now. A part
 * revealed with its failure or the offline note is no longer finished once its read sets out again,
 * so its skeleton stands again rather than a blank; one revealed with its content stays revealed.
 */
function partOf(shown: number, place: number, finished: boolean, landed: boolean) {
  return { finished: shown >= place && finished, landed: shown >= place && landed };
}

/**
 * While the group is on its way, the reads its tabs draw from set out beside it: the deck for the
 * kind the menu stands on — a notice's card's, if it brought one — Fill in and the live yeses.
 */
function ReadingAhead({
  groupId,
  sport,
  kind,
}: {
  readonly groupId: string;
  readonly sport: Sport;
  readonly kind: GameIntent | undefined;
}) {
  const chosen = useGameIntent((state) => state.intent);
  useReadGroupGamesAhead(groupId, sport, kind ?? chosen);
  return null;
}

/** The scrolled tabs drawn for the filter's sport; Games lays itself out. */
function TabBody({
  tab,
  group,
  sport,
  inView,
  friendsTab,
}: {
  readonly tab: GroupTab;
  readonly group: Group;
  readonly sport: Sport;
  readonly inView: boolean;
  /** What the page's menu asks the Friends court — see the module note. */
  readonly friendsTab: Ref<FriendsTabHandle>;
}) {
  switch (tab) {
    case 'games':
      // Never drawn here: Games lays itself out, outside this scroller — see the module note.
      return null;
    case 'fillIn':
      return <FillInBoard groupId={group.id} sport={sport} inView={inView} />;
    case 'youreIn':
      return (
        <YoureInBoard
          groupId={group.id}
          sport={sport}
          inView={inView}
          empty={<YoureInTab group={group} />}
        />
      );
    case 'friends':
      return <FriendsTab group={group} sport={sport} handle={friendsTab} />;
  }
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  tabs: { marginHorizontal: theme.size.gutter },
  fill: { flex: 1 },
  // The deck while another tab is on: kept, and not laid out.
  gone: { display: 'none' },
  body: { padding: theme.size.gutter, gap: theme.space.sm },
  // Over the page's bottom corner, at the gutter (play 46) — above the bar's reach, set where
  // it is read.
  postAGame: { position: 'absolute', right: theme.size.gutter },
});
