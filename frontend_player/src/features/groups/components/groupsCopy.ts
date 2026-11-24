/**
 * **The groups feature's fixed sentences** — every word a screen says that quotes no value. The
 * sentences that compose values (*11 members · Coach Andrzej approves joins*) are functions in
 * `groupsPresentation.ts`, beside this.
 *
 * **This module imports nothing, on purpose.** The feature barrels form a cycle — `groups` reads
 * `onboarding`'s sport names, `onboarding` reaches `auth`, `auth` the shell, and the shell draws
 * Groups — and a component that reads its copy at module load inside that cycle would read it
 * before it was defined. A module with no imports is fully evaluated the moment anything asks for
 * it, whichever way the cycle was entered.
 */

export const GROUPS_COPY = {
  list: {
    newGroup: '+ New',
    newGroupLabel: 'New group',
    join: 'Join',
    joinLabel: 'Join a group',
    empty: 'No groups yet — join or create one for the people you already play with',
  },
  newGroup: {
    title: 'New group',
    back: 'Back to Groups',
    name: 'Name',
    namePlaceholder: 'Give it any name…',
    homeClub: 'Home club',
    homeClubPlaceholder: 'Search clubs by name…',
    noClubNote: 'Only clubs in Raketa can be a home club.',
    setAsHome: 'Set as home',
    change: 'Change',
    changeLabel: 'Change the home club',
    whoCanJoin: 'Who can join',
    anyone: 'Anyone',
    peopleIApprove: 'People I approve',
    noSportNote:
      'No sport to pick: the group plays whatever its members are rated in. Everybody sees the sports they play.',
    create: 'Create the group',
    creating: 'Creating the group',
    created: 'Group created',
  },
  joinGroup: {
    title: 'Join a group',
    back: 'Back to Groups',
    field: 'Group, club or link',
    paste: 'Paste',
    pasteLabel: 'Paste a link',
    clearLabel: 'Clear the search',
    noGroupsHere: 'No groups here yet',
    nothingAtLink: 'Nothing at that link',
  },
  group: {
    back: 'Back to Groups',
    /** One code for *no such group* and *not one of yours* — both have one remedy. */
    refused: {
      group_not_found: 'This group isn’t one of yours.',
    },
    /**
     * The page's four tabs (Q125, #847) — no counts: nothing claims news that does not exist.
     * *You’re in* takes a lower-case *i* and the curly apostrophe, like *Fill in* (split mock 3).
     */
    tabs: { games: 'Games', fillIn: 'Fill in', youreIn: 'You’re in', friends: 'Friends' },
    /**
     * **The kinds a tab's menu picks between** (#861, PRD #859), keyed by `GameIntent` — Friends'
     * lines, and the kind its selected tab is spoken with: *Friends, Competitive*.
     */
    kinds: { competitive: 'Competitive', forFun: 'For fun' },
    /** The header is the door to Info (Q125): the tile, the name and the line under it. */
    openInfo: 'Opens Info',
  },
  /** The fast filter (play 41–42). */
  filter: {
    pillHint: 'Shows this group for another sport you play',
    /** A pill whose only other choice is *+ Another sport* (#731) — there is no sport to switch to. */
    pillHintAnother: 'Offers another sport to rate',
    /** The bar's last way out (#731, ADR-0200 §4): drawn with its plus, spoken without it. */
    anotherSport: 'Another sport',
    anotherSportDrawn: '+ Another sport',
  },
  /** The Games tab's card (play 14–17, 39). */
  games: {
    justYou: 'Just you so far',
    nothingPicked: 'Nothing picked right now',
  },
  /**
   * The group's starting card (play 45–47), on You’re in since #847 — Fill in's until then — and the
   * floating *+ Post a game* over that tab.
   */
  youreIn: {
    alone: 'No games yet — it’s just you',
    others: 'No games yet',
    line: 'Post the first game and it is the first thing people see when they arrive with the link. Or send the link and let somebody else post.',
    postAGame: 'Post a game',
    /** Drawn with its plus; spoken without it, as `postAGame`. */
    postAGameDrawn: '+ Post a game',
  },
  /** The Friends tab and the Friends screen (play 49–55). */
  friends: {
    yourSide: 'Your side',
    theirSide: 'Their side',
    /** The reader's seat, drawn as its three letters over their Level. */
    you: 'You',
    addFriends: '+ Friends',
    addFriendsLabel: 'Pick friends',
    title: 'Friends',
    nobody: 'Nobody you know here yet',
    emptySeatHint: 'Opens Friends',
    /** A seated friend's face: a tap picks it for a swap, the next tap on another swaps them. */
    swapHint: 'Tap another friend to swap them',
    swapWithHint: 'Swaps the two of them',
  },
  /** The link's two doors, on every dark card of the page. */
  link: {
    share: 'Share the link',
    copy: 'Copy link',
    /** Info's link card draws the two doors short, beside the link (play 57, 60); spoken whole. */
    shareShort: 'Share',
    copyShort: 'Copy',
    copied: 'Link copied',
    notCopied: 'Couldn’t copy the link',
  },
  /** Info, the group's own screen, opened from the page's header (play 57–60, club 20; #514, Q125). */
  info: {
    back: 'Back to the group',
    /** The members row's policy line — who answers a request, from where the reader stands. */
    anyoneCanJoin: 'anyone can join',
    /** A search row's line for a group that asks — whoever answers (#529). */
    needsApproval: 'Needs approval',
    youApprove: 'you approve joins',
    ownerApproves: 'the owner approves joins',
    /** An official group's read names nobody; its Administrator answers (#519). */
    administratorApproves: 'the administrator approves joins',
    membersHint: 'Opens Members',
    approve: 'Approve',
    editGroup: 'Edit group',
    editGroupLine: 'Name and who can join',
    delete: 'Delete the group',
    deleting: 'Deleting the group',
    leave: 'Leave the group',
    leaving: 'Leaving the group',
    /** The confirmations name the moment; the act is named once, by the control that does it. */
    deleteTitle: 'Delete this group?',
    deleteBody:
      'Nobody else is in it. Its link stops working, and the group can’t be brought back.',
    deleteClose: 'Keep the group',
    leaveTitle: 'Leave this group?',
    /** An Owner leaving with other members in it — ADR-0183 §7's handover, said before it happens. */
    leaveHandover: 'It passes to whoever has been in it longest, with the requests waiting.',
    rejoinAnyone: 'You can join again any time with its link.',
    rejoinAsk: 'To come back, you ask to join again.',
    leaveClose: 'Stay in the group',
    deleted: 'Group deleted',
    left: 'You left the group',
  },
  /** Members (play 61). No friend tag: there is no friends feature (PRD #500). */
  members: {
    title: 'Members',
    back: 'Back to the group',
    admin: 'admin',
    /**
     * The score tag, spoken — *reliability 92, Very high*; the tag itself draws a spark and the
     * figure on its band's tint (#660). The band's word is `player_record`'s.
     */
    reliability: 'reliability',
    /** A row's hint: a tap opens the record, and the row's label already says whose. */
    openYours: 'Opens your record',
    openTheirs: 'Opens their record',
    /** Who runs an official group, where nobody does now: the club holds it (ADR-0183 §3). */
    noAdministrator: 'no administrator right now',
  },
  /** Edit group — the New group form's two cards and Save (no mock; #514). */
  editGroup: {
    title: 'Edit group',
    back: 'Back to the group',
    save: 'Save',
    saving: 'Saving the group',
    saved: 'Saved',
    admittedLine: 'Everybody who was waiting is in the group now.',
    /** The check before a save that switches People I approve to Anyone (#529). */
    anyoneTitle: 'Let anyone join?',
    anyoneBody:
      'Selecting Anyone allows anyone to join the group, including players with pending requests.',
    anyoneClose: 'Keep People I approve',
  },
  /**
   * **Home's Hottest groups** ([#800](https://github.com/Raketa02/Raketa/issues/800); the words
   * §31.1–§31.4): the row, its card, the group sheet and the withdraw sheet. The marks before the
   * tags — ▲ and + — are drawn, never characters.
   */
  hottest: {
    /** FOR YOU's line (#820) — its title, and what it is named: the row was *HOTTEST GROUPS*. */
    line: 'Groups heating up',
    /** The open line's footer link (#823), the frame drawing its chevron: *All groups ›*. */
    allGroups: 'All groups',
    /** Spoken — the page it opens, the drawn words first (a call: §31.1 writes no name for it). */
    allGroupsLabel: 'All groups heating up',
    /** The Groups heating up page (#823; §31.14). */
    page: {
      title: 'Groups heating up',
      back: 'Back to Home',
      /** The spinner's spoken name while the first page reads. */
      reading: 'Reading groups heating up…',
      /** A list read empty — no group of 3 is left (a call: the line hides then, so it is rarely met). */
      nobody: 'No groups heating up right now',
    },
    /**
     * *Your games*, for a reader in no group, in place of *Play finds you one.* (§31.1) — pointing at
     * the line just below, which starts open for them (#820, Q38).
     */
    groupless: 'Join a group to get games — see Groups heating up, just below.',
    tag: { HOTTEST: 'HOTTEST', GROWING: 'GROWING' },
    /** The tags, spoken. */
    tagSpoken: { HOTTEST: 'hottest', GROWING: 'growing' },
    gamesThisWeek: 'games this week',
    /** One reads *game this week* (§31.2, a call). */
    gameThisWeek: 'game this week',
    players: 'players',
    /** The chip (§31.2) and the sheet's button (§31.3), each by the reader's relation. */
    chip: { join: 'Join', ask: 'Ask to join', requested: 'Asked', in: 'You’re in' },
    openGroup: 'Open group',
    /** The sheet's identity row: *Anyone* · *People I approve*. */
    policy: { ANYONE: 'Open group', PEOPLE_I_APPROVE: 'Closed group' },
    statPlayers: 'players · new this month',
    oneFriend: '1 of your friends plays here',
    /** The card's door and the chips' hints, spoken. */
    opensSheet: 'Opens the group',
    opensGroup: 'Opens the group’s page',
    opensWithdraw: 'Opens Withdraw request',
    /** The withdraw sheet (§31.4). */
    withdraw: 'Withdraw request',
    /** The withdraw sheet's ×, spoken (a call: §31.4 writes no name for it). */
    keepRequest: 'Keep the request',
    /** Its title for an Owner who can no longer be named — the runner unsaid (a call). */
    waitingForAnswer: 'Waiting for an answer',
  },
  /** What an official group's rows and header say beside its name — spoken; `OfficialMark` draws it (#529). */
  official: 'official',
  action: {
    join: 'Join',
    ask: 'Ask to join',
    requested: 'requested · waiting',
    in: 'you’re in',
  },
  retry: 'Try again',
} as const;
