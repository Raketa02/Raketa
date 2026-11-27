/**
 * **Every fixed word a group's Fill in and You’re in tabs say** — a row's lines and its doors, and
 * each tab's empty line and spinner ([#557](https://github.com/Raketa02/Raketa/issues/557), split by
 * [#847](https://github.com/Raketa02/Raketa/issues/847); the screens A3; mocks 12–13, split mocks 1
 * and 2). Neither tab has a heading: the tab's name does that job. Import-free, as
 * `proposalsCopy.ts` is: the group page reads the tabs' words at module load. The sentences composed
 * from a value are `fillInPresentation.ts`.
 */

export const FILL_IN_COPY = {
  /** After a For fun game's title: *Padel · Saturday 16:00 · friendly*. */
  friendly: 'friendly',
  /** A rescue's subtitle, before the cut-off: *fills by Fri 16:00*. */
  fillsBy: 'fills by',
  /** After it: the seat waits until the game starts. */
  offeredUntilTheStart: 'offered until the start',
  /** A yes's subtitle while its game fills: *book by Sat 13:00*. */
  bookBy: 'book by',
  withdraw: 'Withdraw',
  /** A rescue's open seat, drawn in its dashed square. */
  openSeat: '?',
  openSeatSpoken: 'An open seat',
  /** Where a row's upper block goes. */
  rowHint: 'Opens the game’s details',
  /** A poster's hold. */
  holdHint: 'Hold to open their record',
  /** Fill in with no rescue — always this line, never the starting card (split Q3b). */
  noSeats: 'No seats to fill right now',
  /** You’re in with no yes, while Fill in has a seat or could not say (split Q3). */
  noYeses: 'You haven’t said yes to a game here yet',
} as const;
