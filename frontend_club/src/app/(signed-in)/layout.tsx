import type { ReactNode } from 'react';

import { placeOf } from '@/features/club-details/mappers';
import { getClub } from '@/features/club-details/queries';
import { SignOutButton } from '@/features/sign-in/components/SignOutButton';
import { SITE_COPY } from '@/ui/copy';
import { Frame } from '@/ui/Frame';
import { TopBar } from '@/ui/TopBar';

const { frame } = SITE_COPY;
const PAGES = [
  { href: '/overview', label: frame.pages.overview },
  { href: '/groups', label: frame.pages.groups },
  { href: '/administrators', label: frame.pages.administrators },
] as const;

/**
 * **The signed-in frame.** Reading the club redirects to sign-in when there is no session, so
 * nothing under this layout draws for a browser that isn't signed in. Each page reads through
 * the same guard, because a layout is not re-run on every navigation.
 */
export default async function SignedInLayout({ children }: { children: ReactNode }) {
  const club = await getClub();
  return (
    <Frame
      bar={
        <TopBar
          home="/overview"
          label={frame.pagesLabel}
          items={PAGES}
          club={{ name: club.name, place: placeOf(club), href: '/details', title: frame.clubTitle }}
          signOut={<SignOutButton />}
        />
      }
    >
      {children}
    </Frame>
  );
}
