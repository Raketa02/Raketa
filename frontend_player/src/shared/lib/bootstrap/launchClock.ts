/**
 * **The launch's clock** — when the drawn splash fades, and how long it takes
 * ([ADR-0209](../../../../../docs/adr/0209-a-drawn-splash-opens-the-app-and-startup-runs-behind-it.md)
 * §3). Every time is measured from the splash's first layout, which is also when the launch window
 * is let go.
 *
 * The times are the product owner's brief (`docs/specs/splash-screen/`), not the design system's
 * motion scale: they belong to one picture, played once per process.
 */
export const LAUNCH_CLOCK = {
  /**
   * The fade's earliest start: the ball has rested on the dot since 1.68 s, and the word has stood
   * still since 1.78 s (`splashStillAt`).
   */
  fadeAt: 2600,
  /** The same under reduced motion: the lockup in place almost at once, and a brief hold. */
  fadeAtReduced: 900,
  /** The fade itself: the whole splash's opacity, linear, after which the splash unmounts. */
  fade: 500,
  /** The glow coming on, over the ball's first fall, so the flat launch window lightens into it. */
  glowIn: 390,
  /**
   * The lockup coming in — the word and its dot, in place — once the splash has laid out and the
   * wordmark's face is there. **Under reduced motion only**, the brief's *"almost instantly"*: under
   * full motion the ball and the letters bring the lockup in on the motion's own clock (#856,
   * `domain/splashMotion.ts`).
   */
  lockupIn: 150,
  /**
   * **The longest the motion waits for the wordmark's face**, from the splash's first layout. A face
   * there at the start — a release build reads it from the bundle in milliseconds — starts the motion
   * on that layout; one still on its way — a debug build fetches it from the dev server — is waited
   * for, so its seven letters are never set while the ball is in the air, and past this the ball
   * goes without them and they come in late, over `lockupIn`. Short enough that the motion is still
   * by 2.38 s, before the fade's earliest start.
   */
  faceWait: 600,
} as const;

/** What the fade waits for, besides its earliest start. */
export interface FirstScreen {
  /** The sequence resolved or rejected, so the tree or the startup failure is mounted. */
  readonly settled: boolean;
  /** That tree has laid out underneath the splash. */
  readonly laidOut: boolean;
  /** How many screens underneath still say they are blank (`useSplashHold`). */
  readonly holds: number;
}

/**
 * **The first screen is ready** — the second of the fade's two conditions. *Ready* never means its
 * data has arrived: a screen is laid out with its own placeholders. It means only that there is a
 * screen and that none of it says it is blank.
 */
export function firstScreenReady({ settled, laidOut, holds }: FirstScreen): boolean {
  return settled && laidOut && holds === 0;
}
