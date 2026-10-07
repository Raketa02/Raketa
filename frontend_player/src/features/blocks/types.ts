/**
 * The blocks feature's only public surface
 * ([#587](https://github.com/Raketa02/Raketa/issues/587);
 * [ADR-0193](../../../../docs/adr/0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md)).
 *
 * **`player_record` draws `BlockRow`** at the foot of every record but your own, from the record's
 * own `blockedByYou`: the record says whether the reader blocked its subject, and this feature owns
 * the act. **The shell composes `BlockedPlayersRow`** into the You tab's ACCOUNT group, and the
 * route file under `you/` mounts `BlockedPlayersScreen`.
 */

export { BlockRow, type BlockRowProps } from './components/BlockRow';
export { BlockedPlayersRow, type BlockedPlayersRowProps } from './components/BlockedPlayersRow';
export { BlockedPlayersScreen } from './components/BlockedPlayersScreen';

/**
 * The feature's words, exported for the suites that walk the record and the You tab: a test
 * asserting a sentence it spelled itself passes the day the screen stops saying it.
 */
export {
  BLOCKS_COPY,
  blockRowLabel,
  blockSheetBody,
  blockSheetTitle,
  blockedCountLine,
  unblockRowLabel,
} from './components/blocksCopy';
