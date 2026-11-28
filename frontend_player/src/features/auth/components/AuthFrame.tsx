/**
 * **The sign-in screen's chrome, as a piece** — the paper, the scroll that keeps a form reachable
 * over the keyboard and at large text, and the header: *RAKIETA* over the screen's title.
 *
 * It was drawn twice, once by sign-in and once by sign-up, with two copies of one style sheet.
 * *Forgot password?* added four screens that are the same screen asking something else
 * ([#515](https://github.com/Rakieta02/Rakieta/issues/515): *every screen is built from the sign-in
 * screen's existing pieces; nothing is duplicated*), so the chrome is here once, and each screen
 * owns only what it asks.
 *
 * **`lead` is the one addition**: a sentence under the title for a screen that has to say what it
 * does — *we'll send you a link and a code*, *if that email has an account* — which sign-in and
 * sign-up never needed. `tiny` in `muted`, because it is read once and then the form is the
 * screen.
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

import { useState, type ReactNode } from 'react';
import {
  ScrollView,
  StyleSheet,
  Text,
  View,
  type NativeScrollEvent,
  type NativeSyntheticEvent,
  type ScrollViewProps,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { windowResizesForKeyboard } from '@/shared/lib/platform';
import { theme } from '@/shared/ui';

import { AUTH_EYEBROW } from './authPresentation';

/**
 * #529's three props, here once so the stage (`AuthStage`) and this frame cannot drift apart on the
 * keyboard. iOS: the keyboard is an inset on the scroll, set natively, so the form never moves when
 * the keyboard's height does; Android's window resizes for it and ignores the inset. A tap on a
 * control lands while the keyboard is up, and a drag puts it away — the form must stay reachable
 * when large text makes it taller than the screen.
 */
const FORM_SCROLL = {
  testID: 'auth-frame',
  automaticallyAdjustKeyboardInsets: true,
  keyboardShouldPersistTaps: 'handled',
  keyboardDismissMode: 'on-drag',
} as const;

export type FormScrollProps = Pick<
  ScrollViewProps,
  'contentContainerStyle' | 'bounces' | 'overScrollMode' | 'children'
>;

/**
 * **The scroll a form lives in, on both auth frames** — `FORM_SCROLL`'s props, and one repair.
 *
 * **On Android it is mounted afresh when the keyboard's going puts its offset back.** The window
 * shrinks for the keyboard, so with the keyboard up the form can scroll; a drag scrolls it and puts
 * the keyboard away, the window grows back, and Android puts the offset back to the top itself. Under
 * the New Architecture (React Native 0.76) the shadow tree keeps the offset the drag left, so every
 * control in the form is *measured* that far above where it is drawn — and a press is measured: a
 * finger that trembles while it is down reads as sliding off the button, and the press is cancelled.
 * *Sign in* took several taps on an Android phone and one on an iPhone. Asking the scroll to go where
 * it already is does not mend it — React Native has already sent that offset once and will not send
 * it again — so the scroll is mounted afresh, which starts it from a true nought.
 *
 * **A scroll event while the form fits is that putting-back**, since nothing that fits can be
 * scrolled, and it is the one moment this acts. What it costs is a field's own state: a password
 * shown with *Show* is hidden again. Form values are the screens', above this, and stay.
 */
export function FormScroll({ children, ...props }: FormScrollProps) {
  const [mount, setMount] = useState(0);

  const onScroll = ({ nativeEvent }: NativeSyntheticEvent<NativeScrollEvent>) => {
    if (!windowResizesForKeyboard()) return;
    if (nativeEvent.contentSize.height <= nativeEvent.layoutMeasurement.height) {
      setMount((n) => n + 1);
    }
  };

  return (
    <ScrollView key={mount} {...FORM_SCROLL} {...props} onScroll={onScroll}>
      {children}
    </ScrollView>
  );
}

export interface AuthFrameProps {
  readonly title: string;
  /** A sentence under the title, for a screen whose question is not obvious from it. */
  readonly lead?: string;
  readonly children: ReactNode;
}

export function AuthFrame({ title, lead, children }: AuthFrameProps) {
  return (
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      <FormScroll contentContainerStyle={s.content}>
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
      </FormScroll>
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
