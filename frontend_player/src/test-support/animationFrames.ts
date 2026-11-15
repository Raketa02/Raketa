/**
 * Animation frames a screen's distance apart — for the test process only.
 *
 * ## What this fixes
 *
 * `react-native-reanimated`'s `setUpTests()` replaces `requestAnimationFrame` with a `setTimeout(…, 0)`,
 * and React Native's `Animated` asks it for every frame of a JS-driven move — which every
 * `useNativeDriver: true` move is under jest, where there is no native driver. On jest's fake clock
 * a nought-delay timer set during a tick lands a millisecond later, so a move drew a frame every
 * millisecond of the suite's clock: sixteen for each frame a 60 Hz screen draws.
 *
 * That was harmless while every animation ended. Sign-in's hero loop (#787) does not, and
 * `expo-router/testing-library` runs every pending timer on each navigation — up to the last one,
 * which is Query's five-minute collection whenever a query has lost its observers. A test that
 * signed out, or was sent to sign in, landed on the loop and ran five minutes of it, frame by
 * frame, before its next line: about 100,000 frames and 14 s of a 5 s budget on this machine,
 * and the reason six router suites timed out on CI (`forgotPassword`, `onboardingFlow`,
 * `invitationLink`, `groupLink`, `startPlaying`, `theShell`).
 *
 * ## Why this, and not a longer timeout
 *
 * Sixteen milliseconds is what a frame is on the phone, so a move still lands where it lands and
 * when it lands; it is only drawn as often as a screen would draw it. The sweep's length is the
 * harness's and Query's, and the loop is the product's — neither is changed here, and the tests
 * that walk the loop on purpose read the same drawing at the same moments.
 *
 * Not app code — nothing under `src/` imports this.
 */

/** One frame of a 60 Hz screen, in the suite's milliseconds. */
export const FRAME_MS = 16;

/**
 * Draw a frame every `FRAME_MS` of whichever clock the suite is on. Called once, from
 * `jest.setup.js`, after reanimated's own setup — which is what it replaces.
 *
 * `setTimeout` is read at each call, so a suite on fake timers gets the fake one; the frame's
 * time is `performance.now()`, as reanimated's mock gave it.
 */
export function drawFramesAScreenApart(): void {
  globalThis.requestAnimationFrame = (callback: FrameRequestCallback): number =>
    setTimeout(() => callback(globalThis.performance.now()), FRAME_MS) as unknown as number;
  globalThis.cancelAnimationFrame = (handle: number): void =>
    clearTimeout(handle as unknown as ReturnType<typeof setTimeout>);
}
