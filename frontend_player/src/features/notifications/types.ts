/**
 * The notifications feature's only public surface.
 *
 * Two screens' worth of things and one hook the authenticated tree calls.
 * Everything else — the use-cases, the mapper, the wire adapter, the store — is
 * internal: a caller that wanted one of them would be building a second place
 * that asks the OS, and there is exactly one.
 *
 * Nothing here is read by Now, and nothing here may be. `ADR-0061`'s promise is
 * that refusing notifications costs a player the message and never a card, and
 * `nowDiscipline.test.ts` keeps that by walking Now's own source for any mention
 * of the OS. This surface exists for `src/app/` and for the act that will raise
 * the sheet, and for nobody else.
 */

export { NotificationExplainerScreen } from './components/NotificationExplainerScreen';
export {
  NotificationExplainerSheet,
  type NotificationExplainerSheetProps,
} from './components/NotificationExplainerSheet';

/**
 * Re-stating this phone's address once per app session, for a player who has
 * already said yes. Called by `(app)/_layout.tsx`, which is the one file that
 * knows the player is in the app.
 */
export { useDeviceRegistration } from './hooks/useDeviceRegistration';

/**
 * The standby occasion. `ADR-0061`'s second ask, with no act to raise it yet —
 * see the hook.
 */
export {
  useStandbyJoinExplainer,
  type StandbyJoinExplainer,
} from './hooks/useStandbyJoinExplainer';
