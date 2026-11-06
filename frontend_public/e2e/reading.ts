import type { APIRequestContext, Page } from '@playwright/test';

/**
 * **What a messenger, a store or a browser reads off a page**, for the specs that read the same
 * things off more than one page.
 */

/** WhatsApp's link fetcher, and a user agent no list of bots names. */
export const MESSENGERS = [
  'WhatsApp/2.24.6.77 A',
  'Mozilla/5.0 (compatible; SomeNewMessenger/1.0)',
];

/**
 * The `<head>` of the HTML the server sends, and the tags in it by `property` or `name`. A
 * messenger runs no JavaScript and reads `<head>`, so this reads the HTML and nothing else
 * (ADR-0187 §4).
 */
export async function headOf(request: APIRequestContext, path: string, userAgent: string) {
  const response = await request.get(path, { headers: { 'user-agent': userAgent } });
  const html = await response.text();
  const head = html.slice(0, html.indexOf('</head>'));
  const tags = new Map<string, string>();
  for (const [tag] of head.matchAll(/<meta\s[^>]*>/g)) {
    const key = /(?:property|name)="([^"]+)"/.exec(tag)?.[1];
    const content = /content="([^"]*)"/.exec(tag)?.[1];
    if (key !== undefined && content !== undefined) tags.set(key, decode(content));
  }
  const title = /<title>([^<]*)<\/title>/.exec(head)?.[1];
  return {
    status: response.status(),
    title: title === undefined ? undefined : decode(title),
    tags,
  };
}

function decode(text: string): string {
  return text
    .replaceAll('&quot;', '"')
    .replaceAll('&#x27;', "'")
    .replaceAll('&#39;', "'")
    .replaceAll('&lt;', '<')
    .replaceAll('&gt;', '>')
    .replaceAll('&amp;', '&');
}

/** A PNG's width and height, from its header. */
export function sizeOf(png: Buffer): { width: number; height: number } {
  return { width: png.readUInt32BE(16), height: png.readUInt32BE(20) };
}

/**
 * The Google Play button's address, and the **install referrer** it carries: what Play hands the
 * app on its first launch (`referrer`), read as Play reads it.
 */
export async function googlePlayLink(page: Page) {
  const href = await page.getByRole('link', { name: 'Google Play' }).getAttribute('href');
  const url = new URL(href ?? '');
  const referrer = url.searchParams.get('referrer');
  url.searchParams.delete('referrer');
  return { listing: url.toString(), referrer };
}
