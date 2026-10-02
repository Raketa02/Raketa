import type { ReactNode } from 'react';

import { RequestsWatch } from '@/features/bookings/components/RequestsWatch';
import { requestsBadge } from '@/features/bookings/copy';
import { getRequestCount } from '@/features/bookings/queries';
import { placeOf } from '@/features/club-details/mappers';
import { getClub } from '@/features/club-details/queries';
import { SignOutButton } from '@/features/sign-in/components/SignOutButton';
import { SITE_COPY } from '@/ui/copy';
import { Frame } from '@/ui/Frame';
import type { NavItem } from '@/ui/NavLinks';
import { TopBar } from '@/ui/TopBar';

const { frame } = SITE_COPY;

/**
 * The bar's pages (the screens B1), with a coral count on Bookings while requests wait for an
 * answer.
 */
function pages(waiting: number): readonly NavItem[] {
  return [
    { href: '/overview', label: frame.pages.overview },
    { href: '/bookings', label: frame.pages.bookings, ...requestsBadge(waiting) },
    { href: '/courts', label: frame.pages.courts },
    { href: '/money', label: frame.pages.money },
    { href: '/groups', label: frame.pages.groups },
    { href: '/administrators', label: frame.pages.administrators },
  ];
}
const CLUB_PAGES = [
  { href: '/details', label: frame.clubPages.details },
  { href: '/raketa-settings', label: frame.clubPages.raketaSettings },
] as const;

/**
 * **The signed-in frame.** Reading the club redirects to sign-in when there is no session, so
 * nothing under this layout draws for a browser that isn't signed in. Each page reads through
 * the same guard, because a layout is not re-run on every navigation.
 */
export default async function SignedInLayout({ children }: { children: ReactNode }) {
  const [club, waiting] = await Promise.all([getClub(), getRequestCount()]);
  return (
    <Frame
      bar={
        <TopBar
          home="/overview"
          label={frame.pagesLabel}
          items={pages(waiting)}
          club={{ name: club.name, place: placeOf(club), pages: CLUB_PAGES }}
          signOut={<SignOutButton />}
        />
      }
    >
      <RequestsWatch count={waiting} />
      {children}
    </Frame>
  );
}
