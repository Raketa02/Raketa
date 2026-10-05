/**
 * **Where the notifications screens live** (#559) — named here, beside the screens they reach, and
 * read by the route files too: a path spelled twice is the one that goes stale.
 *
 * - **Notifications** is pushed over the You tab, under its first segment so the You column stays
 *   lit (`paymentRoutes`' reason).
 * - **The recent list** is pushed over Home from the bell, under a `notices` segment the shell counts
 *   as Home's (`shellTabs`' `INSIDE_A_TAB`) — Home's root is the shell's own and has no segment to
 *   nest under, `games/`' and `booking/`' reason.
 */

export const YOU_NOTIFICATIONS_ROUTE = '/you/notifications';

export const NOTICES_ROUTE = '/notices';
