import 'server-only';

/**
 * **A photograph the backend signed a link to**, fetched by this server: the one connection it
 * opens besides the backend's, to where the backend keeps photographs (MinIO locally, S3 when
 * deployed). The browser never opens that link: it would be a picture asked of another site
 * (docs/architecture.md §2), by an address that works for minutes.
 *
 * **The link is used at once and kept nowhere.** It is minted for the one read that carried it
 * and expires within minutes, so a picture made later reads again (#748). `no-store` keeps Next's
 * data cache from writing the photograph to disk: this site holds nothing. A failure is logged
 * by its status, never by the link, which carries its signature.
 */

import { TIMEOUT_MS } from './backend';

/** What a picture can be drawn from: what the backend stores, and the one other Satori decodes. */
const DRAWABLE = ['image/jpeg', 'image/png'] as const;

type Drawable = (typeof DRAWABLE)[number];

function isDrawable(type: string): type is Drawable {
  return (DRAWABLE as readonly string[]).includes(type);
}

export interface Photograph {
  readonly type: Drawable;
  readonly bytes: ArrayBuffer;
}

class PhotographUnavailable extends Error {
  override readonly name = 'PhotographUnavailable';
}

/** The photograph at a signed link, or {@link PhotographUnavailable} for anything but one. */
export async function fetchPhotograph(link: string): Promise<Photograph> {
  if (!/^https?:$/.test(URL.parse(link)?.protocol ?? '')) {
    throw new PhotographUnavailable('A photograph link that is not http(s)');
  }
  let response: Response;
  try {
    response = await fetch(link, { cache: 'no-store', signal: AbortSignal.timeout(TIMEOUT_MS) });
  } catch {
    console.error('[public] photograph storage unreachable');
    throw new PhotographUnavailable('The photograph storage could not be reached');
  }
  const type = (response.headers.get('content-type') ?? '').split(';')[0]?.trim() ?? '';
  if (!response.ok || !isDrawable(type)) {
    console.error(`[public] photograph refused: ${response.status} ${type}`);
    throw new PhotographUnavailable(`The photograph storage answered ${response.status}`);
  }
  return { type, bytes: await response.arrayBuffer() };
}
