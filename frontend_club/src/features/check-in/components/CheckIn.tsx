import { ButtonLink } from '@/ui/Button';
import { Card } from '@/ui/Card';
import { PageHeader } from '@/ui/PageHeader';
import { SectionHeader } from '@/ui/SectionHeader';

import { CHECK_IN_COPY } from '../copy';

import { CheckInDesk } from './CheckInDesk';

const COPY = CHECK_IN_COPY;

/**
 * **Check in** (the screens B6, the mechanics §16.10): the desk, for a club that checks players
 * in. A club that doesn't, here by an old link or a setting switched off, is told where to switch
 * it on.
 */
export function CheckIn({ checksIn }: { checksIn: boolean }) {
  return (
    <>
      <PageHeader caption={COPY.caption} title={COPY.title} />
      {checksIn ? (
        <CheckInDesk />
      ) : (
        <Card labelledBy="off-title">
          <SectionHeader id="off-title" title={COPY.off.title} lead={COPY.off.lead} />
          <div>
            <ButtonLink href="/raketa-settings">{COPY.off.settings}</ButtonLink>
          </div>
        </Card>
      )}
    </>
  );
}
