/**
 * **The site's own words that belong to no feature**: the brand, and the pages every link can
 * end on. A feature's words are in its own `copy.ts`, and a primitive takes its words as props.
 * The brand is Raketa, everywhere (ADR-0187 §8).
 */

export const SITE_COPY = {
  name: 'Raketa',
  /**
   * Every page here is reached by a link, so an address that leads nowhere is a dead link, said
   * as the app says it (#500 story 37).
   */
  notFound: {
    title: 'Nothing at that link',
    lead: 'What it led to may have been deleted. Ask whoever sent it.',
  },
  error: {
    title: 'Something went wrong',
    lead: "We couldn't load this page. Try again in a moment.",
    retry: 'Try again',
  },
} as const;

/** Sentences for the refusals every form can meet, whatever it is for. */
export const COMMON_REFUSALS: Readonly<Record<string, string>> = {
  backend_unreachable: "We couldn't reach the server. Try again in a moment.",
  backend_failed: 'Something went wrong on our side. Try again in a moment.',
  request_invalid: 'Something went wrong on our side. Try again in a moment.',
};

export const FALLBACK_REFUSAL = 'Something went wrong. Try again.';
