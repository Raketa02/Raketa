/**
 * **The notifications feature's only public surface** — You › Account › Notifications, the phone's
 * push, the in-app banner and the recent notices behind the bell on Home
 * ([#559](https://github.com/Raketa02/Raketa/issues/559); the screens A7.2, A9; the mechanics
 * §17.2) — over the backend's Notifications context (#549).
 *
 * The shell composes the row into the You tab's ACCOUNT group, the bell into Home's header, and the
 * host beside the tabs for the session; route files under `you/` and at `notices` mount the two
 * screens. The phone's half — the permission, the token, a push arriving and a push tapped — is
 * behind the platform's `PushPort`: nothing here imports `expo-notifications`. Letting the phone go
 * at sign-out is `auth`'s, the sign-out's first step.
 */

export { NotificationsRow, type NotificationsRowProps } from './components/NotificationsRow';
export { NotificationsScreen } from './components/NotificationsScreen';
export { NoticesScreen } from './components/NoticesScreen';
export { NoticeBell } from './components/NoticeBell';
export { NoticesHost } from './components/NoticesHost';
/** The bell's list, read again — for the shell, once a request it was about is answered on Home. */
export { rereadNotices } from './hooks/notificationKeys';
/**
 * **What opening a notice says when it cannot** — *Level asked*'s questionnaire that did not start
 * (*You have a padel level already.*). The shell hands it to Home's ASKED FOR A LEVEL row (#765),
 * whose button runs the same start, so a failure there says the notice's own sentence.
 */
export { OPEN_NOTICE_WORDS } from './components/openNoticeWords';

/** The words the suites hold the screens to. */
export { NOTIFICATIONS_COPY, NOTIFICATIONS_TITLE } from './components/notificationsCopy';
