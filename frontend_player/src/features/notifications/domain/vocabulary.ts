/**
 * **The notices' codes, spelled here** — held equal to the generated ones in
 * `mappers/wireVocabulary.ts`, so a code the contract adds or renames fails `pnpm typecheck` in the
 * one file whose job is saying so (#559).
 *
 * The wire's own spellings, kept, because the list keys nothing by them yet and the push carries
 * them as they are: a notice's kind — every notice the mechanics §17.2 tells, *the club confirmed*
 * and *couldn't take it* two of them — and where a tap opens it.
 */

/** Every notice a player can be told. */
export type NoticeKind =
  | 'GAME_BOOKED'
  | 'WAITING_FOR_THE_CLUB'
  | 'WAITING_FOR_A_PAYMENT'
  | 'TIME_TO_PAY_RAN_OUT'
  | 'CONFIRM_PAYMENT'
  | 'GAME_CALLED_OFF'
  | 'SOMEONE_LEFT'
  | 'REFUNDED'
  | 'CLUB_CONFIRMED'
  | 'CLUB_COULD_NOT_TAKE_IT'
  | 'NEW_GAME'
  | 'POST_DID_NOT_FILL'
  | 'YOU_COMPLETE_IT'
  | 'CHALLENGE'
  | 'FILL_IN_ALERT';

export const NOTICE_KINDS = [
  'GAME_BOOKED',
  'WAITING_FOR_THE_CLUB',
  'WAITING_FOR_A_PAYMENT',
  'TIME_TO_PAY_RAN_OUT',
  'CONFIRM_PAYMENT',
  'GAME_CALLED_OFF',
  'SOMEONE_LEFT',
  'REFUNDED',
  'CLUB_CONFIRMED',
  'CLUB_COULD_NOT_TAKE_IT',
  'NEW_GAME',
  'POST_DID_NOT_FILL',
  'YOU_COMPLETE_IT',
  'CHALLENGE',
  'FILL_IN_ALERT',
] as const satisfies readonly NoticeKind[];

/**
 * Where a tap opens a notice (the screens A9): a booked game's details, a game still filling's — or
 * one that did not fill — and a group's deck with the card on top.
 */
export type Opens = 'BOOKING' | 'PROPOSAL' | 'DECK';

export const OPENS = ['BOOKING', 'PROPOSAL', 'DECK'] as const satisfies readonly Opens[];
