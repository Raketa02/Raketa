import { GROUP_PAGE_COPY, membersLine, sportName, whereItPlays } from '../copy';
import type { LinkedGroup, Sport } from '../mappers';

import styles from './GroupCard.module.css';
import { Monogram } from './Monogram';

/** Each sport's dot, over every sport there is: a fifth fails to compile until it has one. */
const DOTS: Readonly<Record<Sport, string | undefined>> = {
  padel: styles.padel,
  tennis: styles.tennis,
  squash: styles.squash,
  badminton: styles.badminton,
};

/**
 * **The group, as a stranger sees it** (#500 story 47): the tile, the name, where it plays, its
 * sports and how many are in it, laid out as the app's group card (play 38). Each sport dot
 * carries its name, because a stranger has not learnt the app's colours.
 */
export function GroupCard({ group }: { group: LinkedGroup }) {
  return (
    <header className={styles.group}>
      <Monogram monogram={group.monogram} />
      <div className={styles.words}>
        <h1 className={styles.name}>{group.name}</h1>
        <p>{whereItPlays(group.club)}</p>
        <div className={styles.facts}>
          {group.sports.length === 0 ? null : (
            <ul className={styles.sports} aria-label={GROUP_PAGE_COPY.sports}>
              {group.sports.map((sport) => (
                <li key={sport} className={styles.sport}>
                  <span className={`${styles.dot} ${DOTS[sport]}`} aria-hidden="true" />
                  {sportName(sport)}
                </li>
              ))}
            </ul>
          )}
          <p>{membersLine(group.memberCount)}</p>
        </div>
      </div>
    </header>
  );
}
