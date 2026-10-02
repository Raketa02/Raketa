/**
 * **The site's own words that belong to no feature**: the frame's, the error pages', and the
 * refusals every form can meet. A feature's words are in its own `copy.ts`, and a primitive takes
 * its words as props.
 */

export const SITE_COPY = {
  description:
    "A club's desk: its courts and prices on Raketa, its settings, its administrators and its groups.",
  frame: {
    /** The top bar's pages, as a screen reader names the list. */
    pagesLabel: 'Club website',
    pages: {
      overview: 'Overview',
      bookings: 'Bookings',
      courts: 'Courts & prices',
      groups: 'Groups',
      administrators: 'Administrators',
    },
    /** The pages the club's name opens. */
    clubPages: { details: 'Details', raketaSettings: 'Raketa settings' },
  },
  error: {
    title: 'Something went wrong',
    lead: "We couldn't load this page. Try again in a moment.",
    retry: 'Try again',
  },
  notFound: {
    title: 'Nothing at this address',
    lead: 'The page may have moved, or the link is wrong.',
    home: 'Go to Raketa for Clubs',
  },
} as const;

/** Sentences for the refusals every form can meet, whatever it is for. */
export const COMMON_REFUSALS: Readonly<Record<string, string>> = {
  backend_unreachable: "We couldn't reach the server. Try again in a moment.",
  backend_failed: 'Something went wrong on our side. Try again in a moment.',
  request_invalid: 'Something went wrong on our side. Try again in a moment.',
};

export const FALLBACK_REFUSAL = 'Something went wrong. Try again.';
