/**
 * **The row a record ends with** — *Block kuba.w* behind a confirm sheet, or *Unblock kuba.w*
 * once the reader has ([#587](https://github.com/Raketa02/Raketa/issues/587), PRD #571
 * stories 1–5 and 18;
 * [ADR-0193](../../../../../docs/adr/0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md)).
 *
 * `player_record`'s sheet draws it last, on every record but your own, from the record's own
 * `blockedByYou` — so which of the two it is was the server's answer at the last read, and a press
 * re-reads the record rather than flipping the row itself (`useBlockWrites`).
 *
 * ## Block asks first; Unblock does not
 *
 * **A block can cost the blocker a game** — their yeses where the other person is In are taken back
 * and nothing brings them back — so ADR-0193 says the sheet must say what blocking does, *because
 * nothing afterwards will*. The sheet is the departure's shape (`ExitDoor`, `LeaveSheet`): a real
 * modal, focus on the title rather than on the act, the act named once by the button that does it,
 * and *Cancel* under it — the links sheet's two-button shape, its close named *Not now* so two
 * controls never share a name. **Cancel changes nothing**, and closing takes back a block still
 * waiting for the network.
 *
 * **An unblock takes effect on the press.** It costs nothing and moves nothing back — no yes
 * returns — and a second block is one sheet away, so a question in front of it would be friction
 * on the way out of a mistake.
 *
 * ## The sheet is over the record, not instead of it
 *
 * It is the first sheet drawn **over another sheet**: a child of the record's content, so on iOS its
 * native window is presented from the record's, and on Android `OverlayHost` lays it as the next
 * layer up. Whichever row is drawn is hidden from a screen reader while it is up, as `ExitDoor`'s
 * door is — one name on the row and the act, so the first press reaches the row and the second the
 * act. The sheet goes the moment the re-read record says the block stands.
 *
 * ## Beside the friend button, or alone
 *
 * Since [#753](https://github.com/Raketa02/Raketa/issues/753) the record's foot is **one row of two**:
 * `friends`' button on the left and this one on the right, drawn *Block* — the name is spoken, the
 * drawing is the half-width button's word. On somebody the reader blocked it is *Unblock*, **alone
 * and full width** (`friends`' `recordFootOf`), and no offer to befriend them stands beside it.
 *
 * ## Said where it happened
 *
 * A refused block is said on the sheet, with the act still there; a refused unblock under the row
 * (`WriteNote`). Offline, either write waits for the network, and an amber line says so where the
 * press was.
 */

import { useRef, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { behindOverlay, BottomSheet, Button, theme, type FocusTarget } from '@/shared/ui';

import { useBlock, useUnblock, type Reread } from '../hooks/useBlockWrites';

import {
  BLOCKS_COPY,
  blockRowLabel,
  blockSheetBody,
  blockSheetTitle,
  unblockRowLabel,
} from './blocksCopy';
import { WriteNote, type WriteState } from './WriteNote';

const COPY = BLOCKS_COPY;

export interface BlockRowProps {
  /** Whom the record is about — never the reader, whose own record draws no row. */
  readonly playerId: string;
  /** Their whole name, as the record says it. */
  readonly name: string;
  /** Whether the reader has blocked them, as the record last read it. */
  readonly blocked: boolean;
  /**
   * **The record's own re-read**, which a block or an unblock awaits before it settles — so the row
   * flips on the server's next answer. The sheet holds that read; this feature never names its key.
   */
  readonly rereadRecord: Reread;
}

export function BlockRow({ playerId, name, blocked, rereadRecord }: BlockRowProps) {
  const { act: blocking, takeBack } = useBlock(playerId, rereadRecord);
  const unblocking = useUnblock(playerId, rereadRecord);
  const [asking, setAsking] = useState(false);
  const row = useRef<View>(null);

  function ask() {
    blocking.reset();
    setAsking(true);
  }

  // Closing is *don't*: a block the network is still holding is taken back with it.
  function close() {
    setAsking(false);
    takeBack();
  }

  return (
    <>
      <View ref={row} style={s.row} {...behindOverlay(asking)}>
        {blocked ? (
          <Button
            label={COPY.row.unblock}
            accessibilityLabel={unblockRowLabel(name)}
            variant="secondary"
            busy={unblocking.isPending}
            busyLabel={COPY.unblocking}
            onPress={() => unblocking.mutate()}
          />
        ) : (
          <Button
            label={COPY.row.block}
            accessibilityLabel={blockRowLabel(name)}
            variant="secondary"
            onPress={ask}
          />
        )}
        <WriteNote write={unblocking} />
      </View>

      <BlockSheet
        // Gone the moment the re-read record says the block stands.
        visible={asking && !blocked}
        name={name}
        onBlock={() => blocking.mutate(undefined, { onSuccess: () => setAsking(false) })}
        onClose={close}
        write={blocking}
        returnFocusTo={row}
      />
    </>
  );
}

interface BlockSheetProps {
  readonly visible: boolean;
  readonly name: string;
  readonly onBlock: () => void;
  readonly onClose: () => void;
  readonly write: WriteState & { readonly isPending: boolean };
  readonly returnFocusTo: FocusTarget;
}

/** *Block kuba.w?* — what a block does, then **Block** and **Cancel**. */
function BlockSheet({ visible, name, onBlock, onClose, write, returnFocusTo }: BlockSheetProps) {
  return (
    <BottomSheet
      visible={visible}
      onClose={onClose}
      title={blockSheetTitle(name)}
      closeLabel={COPY.sheet.close}
      returnFocusTo={returnFocusTo}
    >
      <Text style={s.body}>{blockSheetBody(name)}</Text>

      <WriteNote write={write} />

      <View style={s.actions}>
        <Button
          label={COPY.sheet.block}
          size="lg"
          busy={write.isPending}
          busyLabel={COPY.sheet.blocking}
          onPress={onBlock}
        />
        <Button label={COPY.sheet.cancel} variant="secondary" size="lg" onPress={onClose} />
      </View>
    </BottomSheet>
  );
}

const s = StyleSheet.create({
  // The record's foot puts the step above it, for both buttons at once.
  row: { gap: theme.space.xs },
  body: { ...theme.type.tiny, color: theme.color.ink, paddingTop: theme.space.sm },
  actions: { gap: theme.space.sm, paddingTop: theme.space.xs },
});
