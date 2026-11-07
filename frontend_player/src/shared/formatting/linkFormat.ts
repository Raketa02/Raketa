/**
 * **A link, as a card draws it** — the address without `https://`, which the mocks never print
 * (play 57, 60; friends 4). Copied, shared and spoken whole; only the drawing drops the scheme.
 *
 * In `shared/` since the third caller ([#756](https://github.com/Raketa02/Raketa/issues/756)): a
 * group's link card on Info and on an official group's page, and the Add friends sheet's friend
 * link — `friends` cannot read `groups` back, since `groups` draws its pills.
 */

export function linkWithoutScheme(link: string): string {
  return link.replace(/^https?:\/\//, '');
}
