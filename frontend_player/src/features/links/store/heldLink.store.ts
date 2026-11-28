/**
 * **The link the app is holding** — one that arrived and has not been answered yet
 * ([#520](https://github.com/Rakieta02/Rakieta/issues/520), PRD #500 story 48).
 *
 * A group link opened before the account exists is kept through sign-up, the naming, the
 * questionnaire and the social steps, and opened once the account is in the app; an invitation's link
 * opened signed out is kept through the sign-in that lets the sheet offer it. So a link outlives the
 * screens it passes and belongs to none of them — and it is a fact about **this process**: not server
 * data, and not the phone's, because a link tapped yesterday is not an instruction today. So it is
 * held in memory and dies with the process, the shape `onboarding`'s set-aside runs and the
 * invitations set aside are for the same reason.
 *
 * **One at a time, the latest winning**: a second link tapped before the first was answered is what
 * the person wants now.
 */

import { create } from 'zustand';

import { sameLink, type IncomingLink } from '../domain/incomingLink';

interface HeldLinkState {
  readonly link: IncomingLink | null;
  /** A link arrived: hold it, in place of any other. */
  readonly hold: (link: IncomingLink) => void;
  /** A link was answered: let it go — if it is still the one held, and not a newer one. */
  readonly letGo: (link: IncomingLink) => void;
  readonly reset: () => void;
}

export const useHeldLinkStore = create<HeldLinkState>((set) => ({
  link: null,
  hold: (link) => set({ link }),
  letGo: (link) =>
    set((state) => (state.link !== null && sameLink(state.link, link) ? { link: null } : state)),
  reset: () => set({ link: null }),
}));
