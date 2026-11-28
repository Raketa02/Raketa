/**
 * **The stage** — sign-in's frame, and sign-up's since #785: a dark hero over the top four tenths of
 * the screen, and a paper sheet with rounded top corners rising over it, holding the form
 * ([#784](https://github.com/Rakieta02/Rakieta/issues/784), PRD #783; design system 12.2).
 *
 * **A new frame beside `AuthFrame`, not a change to it.** The eight other auth screens — the
 * *Forgot password?* flow, the invitation's, *Set your password* and the two links — keep today's
 * paper frame and its *RAKIETA* eyebrow: a short recovery task is not crowded by a hero. Here the
 * hero's wordmark replaces the eyebrow, so the sheet opens on the title alone.
 *
 * ## The sheet is the scrolling part, and the hero stays put
 *
 * The hero is drawn behind the scroll at a fixed height, a share of the **window** (`heroShare`), and
 * the scroll's content starts with that much transparent room before the sheet. So at rest the
 * sheet's top edge sits where the hero ends, and on a short phone, with large text or with the
 * keyboard up, scrolling slides the sheet over the hero — which does not move, because nothing about
 * it is laid out against the scroll or against the screen's height. Android's window shrinks for the
 * keyboard, and a hero sized by the layout would shrink with it.
 *
 * **The keyboard is still an inset on the scroll, set natively** (#529, `AuthFrame`'s note): the form
 * is laid out once, the keyboard changes only the scroll's bottom inset, and the scroll moves only as
 * far as it must to keep the box being typed in above the keys — which, here, is the sheet sliding
 * up over the hero. A bar swap over the keys moves nothing. **No bounce**: pulled past either end,
 * the sheet would lift off the bottom of the screen onto the night, or sink and show its square foot.
 *
 * ## The status bar is light while the stage is in view
 *
 * White icons over the hero, drawn only while `inView` says the stage is the screen on top: a stack
 * keeps this screen mounted under the one pushed over it, and a light bar left mounted would put
 * white icons over *Forgot password?*'s paper. The root layout's dark bar is what is left when this
 * one goes.
 *
 * **And the bar is always over the night.** The sheet can scroll all the way up — a short phone, the
 * keyboard, large text in an uncapped form — and paper under white icons is a clock nobody can read.
 * So a band of the ground the status bar's height is drawn over the scroll, and the sheet slides
 * under it as it would under a header. At rest it is the hero's own top, the same colour.
 *
 * The footer — *New to Rakieta? Create an account*, *Already have an account? Sign in* — sits at the
 * foot of the sheet, however tall the screen, and above the home indicator.
 */

import { StatusBar } from 'expo-status-bar';
import { useContext, type ReactNode } from 'react';
import { StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { SafeAreaInsetsContext, type EdgeInsets } from 'react-native-safe-area-context';

import { theme } from '@/shared/ui';

import { FormScroll } from './AuthFrame';
import { StageHero } from './StageHero';

export interface AuthStageProps {
  /** The sheet's title — *Sign in*. */
  readonly title: string;
  /** The hero's line at its foot. */
  readonly headline: string;
  /** The hero's picture, between the wordmark and the headline — sign-in's deck (#786). */
  readonly picture?: ReactNode;
  /** Drawn over the whole hero but its wordmark — sign-in's *It's a game!* (#787). */
  readonly cover?: ReactNode;
  /** Whether the stage is the screen in view — the status bar is light only while it is. */
  readonly inView: boolean;
  /** The line at the foot of the sheet. */
  readonly footer: ReactNode;
  /** The form, between the title and the footer. */
  readonly children: ReactNode;
}

/** Where nothing provides insets — a screen drawn on its own, as the suites draw it. */
const NO_INSETS: EdgeInsets = { top: 0, right: 0, bottom: 0, left: 0 };

export function AuthStage({
  title,
  headline,
  picture,
  cover,
  inView,
  footer,
  children,
}: AuthStageProps) {
  const { height } = useWindowDimensions();
  // The root's provider, which has known the insets since the app's first frame (`initialMetrics`),
  // so the hero's wordmark is clear of the status bar first time — `TopSafeArea`'s argument against
  // a `SafeAreaView`, which measures itself a frame late. Read as a context rather than through
  // `useSafeAreaInsets`, which throws where there is no provider.
  const { top, bottom } = useContext(SafeAreaInsetsContext) ?? NO_INSETS;
  const heroHeight = Math.round(height * theme.size.stage.heroShare);

  return (
    <View style={s.screen}>
      {inView ? <StatusBar style="light" /> : null}
      <StageHero
        headline={headline}
        height={heroHeight}
        topInset={top}
        picture={picture}
        cover={cover}
      />
      <FormScroll
        contentContainerStyle={[s.content, { paddingTop: heroHeight }]}
        bounces={false}
        overScrollMode="never"
      >
        <View style={[s.sheet, { paddingBottom: Math.max(bottom, theme.space.md) }]}>
          <Text style={s.title} accessibilityRole="header">
            {title}
          </Text>
          {children}
          <View style={s.footer}>{footer}</View>
        </View>
      </FormScroll>
      {/* Over the scroll, so a sheet scrolled all the way up passes under the light status bar's
          night rather than putting paper under it. See the module note. */}
      <View style={[s.statusBand, { height: top }]} pointerEvents="none" />
    </View>
  );
}

const s = StyleSheet.create({
  // The night under everything, so the corners the sheet rounds off show the hero's ground.
  screen: { flex: 1, backgroundColor: theme.color.stageGround },
  content: { flexGrow: 1 },
  sheet: {
    flexGrow: 1,
    backgroundColor: theme.color.paper,
    borderTopLeftRadius: theme.radius.sheet,
    borderTopRightRadius: theme.radius.sheet,
    paddingHorizontal: theme.space.xxl,
    paddingTop: theme.space.xxl,
    gap: theme.space.lg,
  },
  title: { ...theme.type.stageTitle, color: theme.color.ink },
  statusBand: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    backgroundColor: theme.color.stageGround,
  },
  // Pushed to the sheet's foot on a tall phone; straight after the form on a short one.
  footer: { marginTop: 'auto' },
});
