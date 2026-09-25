/**
 * **The sign-in screen's chrome, as a piece** — the paper, the keyboard's avoidance, the scroll
 * that keeps a form reachable at large text, and the header: *RAKETA* over the screen's title.
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
 */

import type { ReactNode } from 'react';
import { KeyboardAvoidingView, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { KEYBOARD_AVOIDANCE } from '@/shared/lib/platform';
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
      <KeyboardAvoidingView
        style={s.flex}
        // The keyboard covers the submit button on iOS otherwise; Android's
        // windowSoftInputMode already handles it and would double-inset.
        behavior={KEYBOARD_AVOIDANCE}
      >
        <ScrollView
          contentContainerStyle={s.content}
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
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

/** The boxes of an auth form, at the form's own spacing. */
export function AuthFields({ children }: { readonly children: ReactNode }) {
  return <View style={s.fields}>{children}</View>;
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  flex: { flex: 1 },
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
