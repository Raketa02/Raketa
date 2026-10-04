import { Redirect, useLocalSearchParams } from 'expo-router';

import { AdministratorArea, parseClubRouteParams } from '@/features/administrator/types';
import { IncomingLinks } from '@/features/links/types';

/**
 * **One club's administrator area** — its stack and its **Groups · You** bar, drawn by the feature
 * (`AdministratorArea`), which also decides whether this account may be here.
 *
 * A club id that does not survive the schema has no area behind it, and `/` is where the entry
 * gate decides where the person belongs instead. A link held since it arrived is answered over the
 * area as over the player's app ([#520](https://github.com/Raketa02/Raketa/issues/520)).
 */
export default function AdministratorAreaLayout() {
  const parsed = parseClubRouteParams(useLocalSearchParams());

  if (parsed === undefined) return <Redirect href="/" />;

  return (
    <>
      <AdministratorArea clubId={parsed.clubId} />
      {/* A held link is answered over the area too (#520) — composed here, beside the area, because
          the links feature reads this one and the area may not read it back. */}
      <IncomingLinks over="administrator" />
    </>
  );
}
