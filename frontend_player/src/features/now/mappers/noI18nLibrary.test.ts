/**
 * v1 ships in English, with no i18n mechanism and no library.
 *
 * `ADR-0075` takes that cost openly — the thirty-six sentences are **rewritten**
 * in Polish rather than translated, and rewording any of the three vocabularies
 * is an app release. The refusal is not about cost: an i18n library's unit is a
 * *string with placeholders*, and the entry shape beside this file rejects that
 * unit for reasons that have nothing to do with translation. Adopting one now
 * would bake in the shape the tables exist to refuse.
 *
 * A dependency is how that decision gets reversed by accident, so the
 * dependency list is what is asserted. `ratingFormat.ts`'s deferral stands: when
 * the app is genuinely localised it becomes one place, and these tables are that
 * place.
 */

import { dependencies, devDependencies } from '../../../../package.json';

const NAMES = /i18n|intl|localiz|localis|lingui|polyglot|gettext|icu-messageformat/i;

describe('no i18n library ships in v1', () => {
  it.each([
    ['dependencies', dependencies],
    ['devDependencies', devDependencies],
  ])('%s name no translation runtime', (_where, list) => {
    expect(Object.keys(list).filter((name) => NAMES.test(name))).toEqual([]);
  });
});
