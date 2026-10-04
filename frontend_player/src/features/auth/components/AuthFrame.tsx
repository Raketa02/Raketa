/**
 * **The sign-in screen's chrome, as a piece** — the paper, the scroll that keeps a form reachable
 * over the keyboard and at large text, and the header: *RAKETA* over the screen's title.
 *
 * It was drawn twice, once by sign-in and once by sign-up, with two copies of one style sheet.
 * *Forgot password?* added four screens that are the same screen asking something else
 * ([#515](https://github.com/Raketa02/Raketa/issues/515): *every screen is built from the sign-in
 * screen's existing pieces; nothing is duplicated*), so the chrome is here once, and each screen
 * owns only what it asks.
 *
 * **`lead` is the one addition**: a sentence under the title for a screen that has to say what it
 * does — *we'll send you a link and a code*, *if that email has an account* — which sign-in and
 * sign-up never needed. `tiny` in `muted`, welcome's body, because it is read once and then the
 * form is the screen.
 *
 * ## The keyboard moves the scroll, never the form
 *
 * **The form is centred on the screen, and the keyboard does not re-centre it** (#529). It was
 * centred in what a `KeyboardAvoidingView` left above the keyboard, so the form's place followed the
 * keyboard's exact height — and on iOS that height changes while the keyboard is up: the bar over
 * the keys is swapped for each field (the email's suggestions, the saved passwords, *Use Strong
 * Password* on a new one) and again when *Show* turns a password's secure entry off or on. Each swap
 * re-padded the view from JavaScript and slid the centred form by half the difference, animated, so
 * every tap that moved focus or showed a password made the screen jump — a blink, on iOS only,
 * because Android's avoidance is the window's own and `KEYBOARD_AVOIDANCE` is off there.
 *
 * **The scroll view takes the keyboard natively instead** (`automaticallyAdjustKeyboardInsets`): the
 * form is laid out once against the whole screen, the keyboard changes only the scroll's bottom
 * inset, animated on the keyboard's own curve, and the scroll moves only as far as it must to keep
 * the field being typed in above the keys. A bar swap moves nothing. What a short screen gives up
 * is the form sliding up whole: *Sign in* may sit under the keys, where the password's *Go* sends
 * the form and a drag puts the keyboard away.
 */

import type { ReactNode } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { theme } from '@/shared/ui';

import { AUTH_EYEBROW } from './authPresentation';

export interface AuthFrameProps {
  readonly title: string;
  /** A sentence under the title, for a screen whose question is not obvious from it. */
  readonly lead?: string;
  readonly children: ReactNode;
}

export function AuthFrame({ title, lead, children }: AuthFrameProps) {
  return (
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      <ScrollView
        testID="auth-frame"
        contentContainerStyle={s.content}
        // iOS: the keyboard is an inset on the scroll, set natively, so the centred form never
        // moves when the keyboard's height does. Android's window resizes for it and ignores this.
        automaticallyAdjustKeyboardInsets
        keyboardShouldPersistTaps="handled"
        // The form must stay reachable when large text makes it taller than the screen.
        keyboardDismissMode="on-drag"
      >
        <View style={s.intro}>
          <View style={s.header}>
            <Text style={s.eyebrow}>{AUTH_EYEBROW}</Text>
            <Text style={s.title} accessibilityRole="header">
              {title}
            </Text>
          </View>
          {lead === undefined ? null : <Text style={s.lead}>{lead}</Text>}
        </View>

        {children}
      </ScrollView>
    </SafeAreaView>
  );
}

/** The boxes of an auth form, at the form's own spacing. */
export function AuthFields({ children }: { readonly children: ReactNode }) {
  return <View style={s.fields}>{children}</View>;
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  content: {
    flexGrow: 1,
    justifyContent: 'center',
    paddingHorizontal: theme.size.gutter,
    paddingVertical: theme.space.xxl,
    gap: theme.space.lg,
  },
  intro: { gap: theme.space.sm },
  header: { gap: theme.space.xxs },
  eyebrow: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: 'uppercase',
  },
  title: { ...theme.type.h1, color: theme.color.ink },
  lead: { ...theme.type.tiny, color: theme.color.muted },
  fields: { gap: theme.space.md },
});
