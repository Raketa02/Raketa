/**
 * **Every fixed word a group's Fill in tab says** — the two sections, a row's lines and its doors
 * ([#557](https://github.com/Raketa02/Raketa/issues/557); the screens A3; mocks 11–13). Import-free,
 * as `proposalsCopy.ts` is: the group page reads the tab's words at module load. The sentences
 * composed from a value are `fillInPresentation.ts`.
 */

export const FILL_IN_COPY = {
  /** *SEATS TO FILL · 1* — the eyebrow uppercases it (A3.1). */
  seatsToFill: 'Seats to fill',
  /** *YOU'RE IN · 1* (A3.2). */
  youreIn: 'You’re In',
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
  reading: 'Reading Fill in',
} as const;
