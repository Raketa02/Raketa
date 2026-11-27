/**
 * **The sign-in screen's text link, as a piece** — *New to Raketa? Create an account*, and now
 * *Forgot password?* under the button and the way back from each recovery screen.
 *
 * **A real 44pt control rather than a line of text.** A `Link` renders a `Text`, whose reachable
 * area is exactly the glyphs — inside a `ScrollView`, a press that drifts a pixel becomes a scroll
 * gesture instead, which is what made the first one take several attempts (6.5). So the target is
 * a `Pressable` tall by its own geometry, not by slop: it sits in a wrapping row, and horizontal
 * slop would be bounded by whatever ends up beside it.
 *
 * Two ways to say where it goes, because two kinds of screen use it: an `href` for the plain
 * moves the two forms always made through `Link`, and `onPress` for the ones that have to choose
 * a verb — back down the stack to sign-in, or a push that carries the email typed so far.
 *
 * **`quiet` is the stage's *Forgot password?*** ([#784](https://github.com/Raketa02/Raketa/issues/784)):
 * `muted` rather than `ink`, and at the end of its row rather than the middle — right-aligned under
 * the password box it is about, where the problem is. Still the same 44pt control.
 *
 * **`busy` is 6.1's busy on a link** ([`decisions.md`](../../../../../docs/specs/busy-indicator/decisions.md)
 * §3.7): Start playing's *Sign out* swapped its word and still took a second press, so one sign-out
 * could be asked twice. Busy, it takes no press, is announced busy, and turns `ActivityIndicator`
 * before its words in their own ink — the button's drawing, at a link's size. The words stay the
 * caller's: pass the busy one as `label`.
 */

import { Link, type Href } from 'expo-router';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

type Target = { readonly href: Href } | { readonly onPress: () => void };

export type AuthLinkProps = Target & {
  /** Muted words before the link — *New to Raketa?* — or nothing. */
  readonly lead?: string;
  /** What the link says, and its accessible name. */
  readonly label: string;
  /** `muted`, and at the end of the row — the stage's *Forgot password?*. See the module note. */
  readonly quiet?: boolean;
  /** Its act is on its way: no press, announced busy, a spinner before the words. See the module note. */
  readonly busy?: boolean;
};

export function AuthLink(props: AuthLinkProps) {
  const { lead, label, quiet = false, busy = false } = props;

  const control = (
    <Pressable
      accessibilityRole="link"
      accessibilityLabel={label}
      accessibilityState={busy ? { busy: true, disabled: true } : undefined}
      disabled={busy}
      onPress={'onPress' in props ? props.onPress : undefined}
      style={({ pressed }) => [
        s.target,
        busy ? s.targetBusy : undefined,
        quiet ? s.targetQuiet : undefined,
        pressed && !busy ? s.pressed : undefined,
      ]}
    >
      {busy ? (
        <ActivityIndicator
          size="small"
          color={quiet ? theme.color.muted : theme.color.ink}
          accessibilityElementsHidden
          importantForAccessibility="no-hide-descendants"
        />
      ) : null}
      <Text style={[s.link, quiet ? s.linkQuiet : undefined]}>{label}</Text>
    </Pressable>
  );

  return (
    <View style={[s.row, quiet ? s.rowQuiet : undefined]}>
      {lead === undefined ? null : <Text style={s.lead}>{lead}</Text>}
      {'href' in props ? (
        <Link href={props.href} asChild>
          {control}
        </Link>
      ) : (
        control
      )}
    </View>
  );
}

const s = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    flexWrap: 'wrap',
    gap: theme.space.xs,
  },
  // The quiet link sits at the end of its row, its words flush with the box's edge above it.
  rowQuiet: { justifyContent: 'flex-end' },
  lead: { ...theme.type.tiny, color: theme.color.muted },
  target: {
    minHeight: theme.size.minTouch,
    justifyContent: 'center',
    paddingHorizontal: theme.space.xs,
  },
  // 6.6's chip value. The two screens this piece came from drew `.6`, the one value that table
  // does not have, and a shared piece is where a stray number stops being one screen's.
  pressed: { opacity: 0.7 },
  // The spinner and the words on one line, a word's gap apart — the button's busy row (6.1).
  targetBusy: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  targetQuiet: { paddingRight: 0 },
  link: { ...theme.type.rlValue, color: theme.color.ink },
  linkQuiet: { color: theme.color.muted },
});
