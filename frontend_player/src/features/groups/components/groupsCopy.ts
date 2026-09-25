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
    required: 'required',
    homeClubPlaceholder: 'Search clubs by name…',
    homeClubHint: 'Start typing a club’s name. Every club in Raketa is here.',
    /** Under the field until a club is chosen (play 6–10). */
    homeClubConsequence:
      'Every group lives at a club: its courts are where the app looks first for this group’s games.',
    noClubNote: 'Only clubs in Raketa can be a home club.',
    setAsHome: 'Set as home ›',
    groupAlreadyHere: 'group already here',
    change: 'Change',
    changeLabel: 'Change the home club',
    whoCanJoin: 'Who can join',
    anyone: 'Anyone',
    peopleIApprove: 'People I approve',
    noSportNote:
      'No sport to pick: the group plays whatever its members are rated in. Everybody sees the sports they play.',
    create: 'Create the group',
    creating: 'Creating the group',
    createNote:
      'You get a link to send to the WhatsApp crowd. When they finish getting rated, they land here.',
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
    /** The page's four tabs (play 43) — no counts: nothing claims news that does not exist. */
    tabs: { games: 'Games', fillIn: 'Fill in', friends: 'Friends', info: 'Info' },
  },
  /** The fast filter (play 41–42). */
  filter: {
    pillHint: 'Shows this group for another sport you play',
    /** The pill's faint chevron, and the bar's once it has unfolded — the fold's direction. */
    unfold: '‹',
    fold: '›',
  },
  /** The Games tab's card (play 14–17, 39). */
  games: {
    justYou: 'Just you so far',
    nothingPicked: 'Nothing picked right now',
  },
  /** The Fill in tab (play 45–47). */
  fillIn: {
    alone: 'No games yet — it’s just you',
    others: 'No games yet',
    line: 'Post the first game and it is the first thing people see when they arrive with the link. Or send the link and let somebody else post.',
    postAGame: 'Post a game',
    /** Drawn with its plus; spoken without it, as `postAGame`. */
    postAGameDrawn: '+ Post a game',
  },
  /** The Friends tab and the Friends screen (play 49–55). */
  friends: {
    competitive: 'Competitive',
    forFun: 'For fun',
    yourSide: 'Your side',
    theirSide: 'Their side',
    /** The reader's seat, drawn as its three letters over their Level. */
    you: 'You',
    addFriends: '+ Friends',
    addFriendsLabel: 'Pick friends',
    title: 'Friends',
    back: 'Back to the group',
    nobody: 'Nobody you know here yet',
    emptySeatHint: 'Opens Friends',
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
  /** The Info tab (play 57–60, club 20; #514). */
  info: {
    /** The members row's policy line — who answers a request, from where the reader stands. */
    anyoneCanJoin: 'anyone can join',
    youApprove: 'you approve joins',
    ownerApproves: 'the owner approves joins',
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
    rejoinAsk: 'To come back, you ask to join again with its link.',
    leaveClose: 'Stay in the group',
    deleted: 'Group deleted',
    left: 'You left the group',
  },
  /** Members (play 61). No friend tag: there is no friends feature (PRD #500). */
  members: {
    title: 'Members',
    back: 'Back to the group',
    admin: 'admin',
    footer: 'Press and hold anyone for the full record.',
    holdHint: 'Press and hold for the full record',
  },
  /** Edit group — the New group form's two cards and Save (no mock; #514). */
  editGroup: {
    title: 'Edit group',
    back: 'Back to the group',
    save: 'Save',
    saving: 'Saving the group',
    saved: 'Saved',
    admittedLine: 'Everybody who was waiting is in the group now.',
  },
  action: {
    join: 'Join',
    ask: 'Ask to join',
    requested: 'requested · waiting',
    in: 'you’re in',
  },
  retry: 'Try again',
} as const;
