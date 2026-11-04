/**
 * **The screens pushed over a tab** — every route in the tab tree but Home's and You's roots, each
 * named for the push transition `TabShell` gives it. The stack's default is `none`, for a replace;
 * a pushed screen keeps what it arrived on underneath, and leaving it should read as coming back
 * out.
 *
 * **A route missing from this list is not an error anywhere but here.** It still opens, with no
 * transition at all: the page it was opened from is swapped for it in one frame, and a screen whose
 * header matches the one underneath, as a group's Info matches its page, reads as a blink. Info,
 * Post a game, a game's details and a rescue each shipped that way, so `pushedScreens.test.ts`
 * holds this list to the file tree in both directions.
 *
 * Names, because `Stack.Screen` matches on the name; a wildcard would put the push on a root too.
 */
export const PUSHED_SCREENS = [
  // ⚡Play's root is pushed over Home (`PLAY_STACK`), so back from it leaves Play.
  'play/index',
  // The groups screens (#512, #513, #514): New group and Join a group are pushed over the Groups
  // list and come back out to it, and a group's page is pushed over the list — or replaces New
  // group once the group exists, so *back* is the list either way.
  'play/new-group',
  'play/join',
  'play/group/[groupId]/index',
  // Pushed over a group's page and come back out to it: Info from its header (Q125), Friends from
  // an empty seat, a game's details and a rescue from the deck or Fill in, and Post a game from
  // Fill in (#553, #557, #558).
  'play/group/[groupId]/info',
  'play/group/[groupId]/friends',
  'play/group/[groupId]/game/[proposalId]',
  'play/group/[groupId]/rescue/[bookingId]',
  'play/group/[groupId]/post',
  // Pushed over Info and come back out to it: Members and Edit group (Q125).
  'play/group/[groupId]/members',
  'play/group/[groupId]/edit',
  // A booked game (#556): its details pushed over Home, its chat and its result pushed over the
  // details. The chat is the one screen the bar stands down on (`shellTabs`).
  'booking/[bookingId]/index',
  'booking/[bookingId]/chat',
  'booking/[bookingId]/result',
  // The recent notices behind Home's bell (#559): pushed over Home, and back is Home — a row opens
  // its game over the list, so back from the game is the list.
  'notices',
  // Every screen behind a row on You: each is pushed over the tab, and backing out returns to the
  // row it was tapped from
  // ([ADR-0179](../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
  // §1). `you/index` is the tab's root, arrived at by a tab press, and takes the shell's `none`.
  'you/passport',
  'you/reliability',
  'you/kind-of-game',
  'you/week',
  'you/area',
  'you/who-you-play-with',
  'you/photos',
  'you/tags',
  'you/intro',
  'you/name',
  'you/games-and-money',
  'you/payments',
  'you/notifications',
  'you/blocked-players',
] as const;
