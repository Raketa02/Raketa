import { ButtonLink } from '@/ui/ButtonLink';
import { CardSection } from '@/ui/PageCard';

import { GET_THE_APP_COPY } from '../copy';
import type { AppLinks } from '../queries';

import styles from './GetTheApp.module.css';

/**
 * **The way in**, on every page a link opens without the app: the two stores, a line saying what
 * to do once installed, and **Open in Raketa** for a phone that has the app but where the link
 * didn't open it (ADR-0187 §4).
 */
export function GetTheApp({ links, next }: { links: AppLinks; next: string }) {
  return (
    <>
      <CardSection>
        <div className={styles.stores} role="group" aria-label={GET_THE_APP_COPY.stores}>
          <ButtonLink href={links.appStore} tone="store">
            {GET_THE_APP_COPY.appStore}
          </ButtonLink>
          <ButtonLink href={links.googlePlay} tone="store">
            {GET_THE_APP_COPY.googlePlay}
          </ButtonLink>
        </div>
        <p className={styles.next}>{next}</p>
      </CardSection>
      <CardSection>
        <ButtonLink href={links.openInRaketa} tone="outline">
          {GET_THE_APP_COPY.openInRaketa}
        </ButtonLink>
      </CardSection>
    </>
  );
}
