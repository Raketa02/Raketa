/**
 * The tab tree: one `Stack` and one bar, both drawn by the shell.
 *
 * A layout route may own a layout, and that is all this is. Why it is a `Stack` rather than
 * `<Tabs>` — the shell keeps no per-tab history — is a decision with an argument, and the
 * argument lives with the component that implements it.
 */

import { TabShell } from '@/features/shell/types';

export default function TabsLayout() {
  return <TabShell />;
}
