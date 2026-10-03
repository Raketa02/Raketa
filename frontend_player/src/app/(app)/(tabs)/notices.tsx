import { NoticesScreen } from '@/features/notifications/types';

/**
 * **The recent notices** — pushed over Home from its bell (#559), under a `notices` segment the shell
 * counts as Home's (`shellTabs`), so the Home column stays lit and *back* is Home.
 */
export default function NoticesRoute() {
  return <NoticesScreen />;
}
