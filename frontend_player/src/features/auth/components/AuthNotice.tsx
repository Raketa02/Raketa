/**
 * The one auth-form control the design system does not specify.
 *
 * **This file used to hold two, and the other one has left.** `AuthField` was the app's only
 * `TextInput` — a text field the design system had never specified, built beside the system
 * because there was nothing to build on. There is now:
 * [6.13](../../../../docs/design-system.md#613-the-text-field) is `shared/ui`'s `TextField`,
 * and these forms are its first caller rather than its second implementation. The placeholder
 * button went the same way earlier, to `Button`; two implementations of one primitive is
 * exactly how the prototype's copies drifted.
 *
 * What remains is here because the system genuinely has no equivalent. A form-level failure
 * banner is not a `Note`: the five note variants are base, mint, coral, amber and info, and
 * none of them means *ended badly*. Adding a red note is a design-system change, in its own
 * commit, with its computed contrast — not something a screen invents on the way past.
 *
 * Every value still comes from the theme: a placeholder is not an excuse for a literal.
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui/theme';

export interface AuthNoticeProps {
  readonly message: string;
}

/** A form-level failure — the ones that belong to no single field. */
export function AuthNotice({ message }: AuthNoticeProps) {
  return (
    <View style={s.notice} accessibilityRole="alert">
      <Text style={s.noticeText}>{message}</Text>
    </View>
  );
}

const s = StyleSheet.create({
  notice: {
    backgroundColor: theme.color.redSoft,
    borderRadius: theme.radius.note,
    paddingHorizontal: theme.space.md,
    paddingVertical: theme.space.sm,
  },
  noticeText: {
    ...theme.type.tiny,
    color: theme.color.red,
  },
});
