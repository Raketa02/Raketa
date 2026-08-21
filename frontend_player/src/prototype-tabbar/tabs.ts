/**
 * PROTOTYPE — throwaway. Answers Raketa02/Raketa#49: "Five glyphs the tab bar has never had".
 * Do not promote any of this to production; the winner gets rewritten properly.
 *
 * The five acts, from `rakieta-now-section-ui-spec.md` §B13. The create tab has no label
 * and is not a peer: 28pt against 16pt, coral against currentColor, `margin-bottom:-4px`.
 */

export type TabKey = 'now' | 'find' | 'create' | 'msg' | 'you';

export type TabSpec = { key: TabKey; label: string | null };

export const TABS: readonly TabSpec[] = [
  { key: 'now', label: 'Now' },
  { key: 'find', label: 'Find' },
  { key: 'create', label: null },
  { key: 'msg', label: 'Inbox' },
  { key: 'you', label: 'You' },
] as const;

/** §B13: label 8.5/600 Archivo. There is no `type` token this small — the tab bar is the
 *  only place it appears, which is itself worth noticing while judging these. */
export const TAB_LABEL_SIZE = 8.5;
