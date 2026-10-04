/**
 * **Switching to Anyone is asked first** (#529) — the sheet a save that turns *People I approve*
 * into *Anyone* opens before anything is sent: *Let anyone join?*, what it does — *anyone can join,
 * including players with pending requests* — and *Save*, which sends it. Closing it, *Keep People I
 * approve*, keeps the form as it is, unsaved.
 *
 * **One sheet for both forms that can do it**: an Owner's Edit group, and an official group's
 * settings in the administrator area, lent from `types.ts` — the switch admits everybody waiting
 * either way, so the two are told the same thing in the same words.
 */

import { StyleSheet, Text, View } from 'react-native';

import { BottomSheet, Button, theme, type FocusTarget } from '@/shared/ui';

import { GROUPS_COPY } from './groupsCopy';

const COPY = GROUPS_COPY.editGroup;

export interface OpenToAnyoneSheetProps {
  readonly visible: boolean;
  /** *Keep People I approve*, a tap outside, or the back gesture — nothing is sent. */
  readonly onClose: () => void;
  /** *Save* — the form goes as it is. */
  readonly onConfirm: () => void;
  /** The form's own *Save*, where a screen reader's focus goes back to. */
  readonly returnFocusTo?: FocusTarget;
}

export function OpenToAnyoneSheet({
  visible,
  onClose,
  onConfirm,
  returnFocusTo,
}: OpenToAnyoneSheetProps) {
  return (
    <BottomSheet
      visible={visible}
      onClose={onClose}
      title={COPY.anyoneTitle}
      closeLabel={COPY.anyoneClose}
      {...(returnFocusTo === undefined ? {} : { returnFocusTo })}
    >
      <Text style={s.body}>{COPY.anyoneBody}</Text>
      <View style={s.act}>
        <Button label={COPY.save} size="lg" onPress={onConfirm} />
      </View>
    </BottomSheet>
  );
}

const s = StyleSheet.create({
  // The exit sheet's measures (`ExitDoor`): its line under the title, and its act under that.
  body: { ...theme.type.tiny, color: theme.color.ink, paddingTop: theme.space.sm },
  act: { paddingTop: theme.space.md },
});
