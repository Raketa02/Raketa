/**
 * **The notices' codes, spelled here** — held equal to the generated ones in
 * `mappers/wireVocabulary.ts`, so a code the contract adds or renames fails `pnpm typecheck` in the
 * one file whose job is saying so (#559).
 *
 * The wire's own spellings, kept, because the list keys nothing by them yet and the push carries
 * them as they are: a notice's kind — every notice the mechanics §17.2 tells — and where a tap
 * opens it. No club confirms a game any more (ADR-0196, #676), so none is about a club's answer.
 */

/** Every notice a player can be told. */
export type NoticeKind =
  | 'GAME_BOOKED'
  | 'WAITING_FOR_A_PAYMENT'
  | 'TIME_TO_PAY_RAN_OUT'
  | 'TIME_TO_FIX_RAN_OUT'
  | 'CONFIRM_PAYMENT'
  | 'FIX_YOUR_CARD'
  | 'GAME_CALLED_OFF'
  | 'SOMEONE_LEFT'
  | 'REFUNDED'
  | 'NEW_GAME'
  /** A club's cancel moved the game to another court, or the club moved it (#671): its booking. */
  | 'GAME_MOVED'
  | 'POST_DID_NOT_FILL'
  | 'YOU_COMPLETE_IT'
  | 'CHALLENGE'
  | 'FILL_IN_ALERT'
  | 'NOT_HERE_YET'
  | 'AT_THE_CLUB'
  | 'HOW_DID_IT_GO'
  | 'IS_THAT_RIGHT'
  | 'WERE_THEY_THERE'
  /**
   * *Get your level so your groups can deal you games.* (#727) — the first notice about no game,
   * opening Home, where its card is (#731).
   */
  | 'GET_YOUR_LEVEL'
  /** *ines.d wants to be your friend* (#745, #753) — opens Home, where its card is. */
  | 'FRIEND_REQUEST'
  /** *kuba.w said yes — you're friends*, or *You and kuba.w are friends now* — opens their record. */
  | 'FRIENDS_MADE'
  /**
   * *kuba.w wants to play padel with you. Get your padel level so kuba.w can add you.* (#749) —
   * opens that sport's questionnaire, through the level pass and its usual return (#758).
   */
  | 'LEVEL_ASKED'
  /**
   * *kuba.w has a padel level — you can seat kuba.w now.* (#749) — opens the Friends tab picker of
   * the group the ask was made from (#758).
   */
  | 'LEVEL_GOT';

export const NOTICE_KINDS = [
  'GAME_BOOKED',
  'WAITING_FOR_A_PAYMENT',
  'TIME_TO_PAY_RAN_OUT',
  'TIME_TO_FIX_RAN_OUT',
  'CONFIRM_PAYMENT',
  'FIX_YOUR_CARD',
  'GAME_CALLED_OFF',
  'SOMEONE_LEFT',
  'REFUNDED',
  'NEW_GAME',
  'GAME_MOVED',
  'POST_DID_NOT_FILL',
  'YOU_COMPLETE_IT',
  'CHALLENGE',
  'FILL_IN_ALERT',
  'NOT_HERE_YET',
  'AT_THE_CLUB',
  'HOW_DID_IT_GO',
  'IS_THAT_RIGHT',
  'WERE_THEY_THERE',
  'GET_YOUR_LEVEL',
  'FRIEND_REQUEST',
  'FRIENDS_MADE',
  'LEVEL_ASKED',
  'LEVEL_GOT',
] as const satisfies readonly NoticeKind[];

/**
 * Where a tap opens a notice (the screens A9): a booked game's details, a game still filling's — or
 * one that did not fill — a group's deck with the card on top, a booked game's result screen
 * (#663), where each step at the court is acted on, Home (#727, #731), for a notice about no
 * game, a player's record (#753), for *You're friends*, and the two an ask for a Level opens
 * (#758): a sport's questionnaire, and a group's Friends picker.
 */
export type Opens =
  | 'BOOKING'
  | 'PROPOSAL'
  | 'DECK'
  | 'RESULT'
  | 'HOME'
  | 'RECORD'
  /** A sport's questionnaire, through the level pass (`LEVEL_ASKED`, #749, #758). */
  | 'QUESTIONNAIRE'
  /** A group's Friends tab picker, in a sport (`LEVEL_GOT`, #749, #758). */
  | 'PICKER';

/** The places a tap opens that are a game's — every one but Home, a record and an ask's two. */
export type GameOpens = Exclude<Opens, 'HOME' | 'RECORD' | 'QUESTIONNAIRE' | 'PICKER'>;

/** The four a game's notice opens — what a push about a game is checked against. */
export const GAME_OPENS = [
  'BOOKING',
  'PROPOSAL',
  'DECK',
  'RESULT',
] as const satisfies readonly GameOpens[];
