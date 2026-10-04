import { GROUPS_COPY as COPY } from '../copy';
import type { GroupAdministrator } from '../mappers';

import styles from './RunBy.module.css';

/** **Who runs a group**: the administrator's name, or *needs an administrator* in amber. */
export function RunBy({ administrator }: { administrator: GroupAdministrator | null }) {
  if (administrator === null) {
    return <span className={styles.needsAdministrator}>{COPY.needsAdministrator}</span>;
  }
  return <>{administrator.name}</>;
}
