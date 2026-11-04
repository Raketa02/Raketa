/**
 * **Members** — who in the group the reader could play the filter's sport with (play 61;
 * [#514](https://github.com/Raketa02/Raketa/issues/514), PRD #500 stories 80–84).
 *
 * Pushed over Info from its members row (Q125). The header is *Members · N* and **the sport pill,
 * sharing the filter's one state** (`SportFilterPage`): a sport picked here is the group page's
 * sport when the player goes back to it. **N is how many rows the list draws for the pill's sport**, so
 * it moves when the sport does — the title reads the list's own query, one key and one request —
 * and the title is the word alone until the list is in, or where there is no sport to list. It
 * carries no eyebrow — the group's name and count over it said nothing the page it was pushed from
 * had not just said (#529) — and the list no heading: the *Play Padel · N* that stood over it gave
 * its count to the title (2026-10-01).
 *
 * **The list is the server's, in the server's order**: only members rated in the sport, the
 * reader first as *You*, then the Owner with the **admin** tag — on an official group, its
 * Administrator who joined as a player (#519) — then newest joined first. Each row is the name,
 * the **score tag** (`PlayerScoreTag`: a spark and the points on the tint of the band the server
 * served, #660) and the admin tag, over the sport's dot and *Padel 2,71*; every row has one, since
 * everyone starts at 100. A block hides nobody here, either way round (ADR-0193 §2). **No friend tag**:
 * there is no friends feature (PRD #500 overrides play 61 by name).
 *
 * ## Who runs it is always here
 *
 * **A member can always find who runs the group** (#529, the product owner's ask) — to know who
 * answers for it, and who to go to. A player group's Owner is a member and leads the list; an
 * official group's Administrator need not play in it, and was on no list. So **a card over the
 * list names them** (`RunnerCard`): the club's tile, their whole nickname and the admin tag, over *runs
 * this group for Ogrody 33* — or the club over *no administrator right now* while the group needs
 * one. It is drawn **wherever the sport's list does not carry their own admin-tagged row**, so
 * nobody is drawn twice, and never for a reader who runs it. It is not a button — an Administrator
 * need not play, so there may be no record to open — and not a member, so the title's count leaves
 * it out (`runnerApart`).
 *
 * ## A tap opens the record
 *
 * **Tapping a row opens the existing player record sheet** for that person — your own row opens
 * your own record, retitled by the sheet's own rule. It was a press and hold, as #514 and play 61
 * asked, with a footer to explain it; the product owner moved it to a tap (2026-10-01) as the more
 * obvious gesture, which also answers #285's objection to the hold — no affordance and no
 * accessibility equivalent — the way the games feature's players card does: the row is a button,
 * every screen reader activates it, and the hint says what it opens. So the footer went with the
 * hold, and so did the custom `longpress` action. Recorded in the feature's design record.
 *
 * ## The Administrator's Members
 *
 * **An official group's Administrator opens the same screen** from the members card on the group's
 * page in the administrator area (#529) — the same header, list, rows and record sheet
 * (`AdministeredMembersScreen`). Two things differ, because somebody who runs a group need not
 * play in it: **the pill lists the sports the group declares**, not the ones the reader is rated in
 * (`useDeclaredSport`), so there is never an *Add Padel* card in place of the list; and the group
 * is the administrator area's read, handed in, since the player's read of a group is its members'.
 * The reader is no row unless they joined as a player, when they are *You*, as anywhere.
 */

import { router } from 'expo-router';
import { useState, type ReactNode } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { sportColour } from '@/features/onboarding/types';
import {
  PlayerRecordSheet,
  PlayerScoreTag,
  type RecordSubject,
} from '@/features/player_record/types';
import { codeMessage } from '@/shared/errors';
import { Card, PlayerPhoto, ScreenHeader, Tag, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { Group, GroupMember } from '../domain/group';
import { adminTagged, runnerApart, type GroupRunner } from '../domain/groupInfo';
import { useDeclaredSport } from '../hooks/useGroupSport';
import { useGroup, useGroupMembers } from '../hooks/useGroups';
import { useReaderId } from '../hooks/useReaderId';

import { AddSportCard } from './AddSportCard';
import { ClubTile } from './ClubTile';
import { GROUPS_COPY } from './groupsCopy';
import {
  memberLine,
  memberName,
  memberRowLabel,
  membersTitle,
  openRecordHint,
  runnerLabel,
  runnerLine,
  runnerName,
} from './groupsPresentation';
import { ROW_FACE } from './peopleRow';
import { ReadFailure } from './ReadFailure';
import { SportFilterFrame, SportFilterPage } from './SportFilterPage';

const COPY = GROUPS_COPY.members;

export function MembersScreen({ groupId }: { readonly groupId: string }) {
  const read = useGroup(groupId);
  const group = read.data;

  return (
    <SafeAreaView style={s.screen} edges={['top']}>
      <SportFilterPage
        {...(group?.declaredSports === undefined ? {} : { declaredSports: group.declaredSports })}
        header={(pill, _cover, sport) => (
          <MembersHeader
            groupId={groupId}
            sport={sport}
            right={group === undefined ? undefined : pill}
          />
        )}
      >
        {(sport, toAdd) =>
          group === undefined ? (
            read.error === null ? null : (
              <View style={s.body}>
                <ReadFailure
                  error={read.error}
                  message={codeMessage(GROUPS_COPY.group.refused, read.error)}
                  onRetry={() => void read.refetch()}
                />
              </View>
            )
          ) : toAdd.length > 0 ? (
            // An official group the reader plays none of the sports of: no list is drawn for one.
            <View style={s.body}>
              <AddSportCard sports={toAdd} />
            </View>
          ) : sport === undefined ? null : (
            <MembersList
              groupId={groupId}
              sport={sport}
              refused={GROUPS_COPY.group.refused}
              group={group}
            />
          )
        }
      </SportFilterPage>
    </SafeAreaView>
  );
}

export interface AdministeredMembersScreenProps {
  readonly groupId: string;
  /** The sports the official group declares — `undefined` while the group is being read. */
  readonly sports: readonly Sport[] | undefined;
  /** What a refused list says, by code — in the Administrator's words, which are not this feature's. */
  readonly refused: Readonly<Record<string, string>>;
}

/** **Members, for the Administrator who runs an official group** — its sports, not the reader's. */
export function AdministeredMembersScreen({
  groupId,
  sports,
  refused,
}: AdministeredMembersScreenProps) {
  const filter = useDeclaredSport(sports);

  return (
    <SafeAreaView style={s.screen} edges={['top']}>
      <SportFilterFrame
        filter={filter}
        header={(pill, _cover, sport) => (
          <MembersHeader groupId={groupId} sport={sport} right={pill} />
        )}
      >
        {(sport) =>
          sport === undefined ? null : (
            <MembersList groupId={groupId} sport={sport} refused={refused} />
          )
        }
      </SportFilterFrame>
    </SafeAreaView>
  );
}

interface MembersHeaderProps {
  readonly groupId: string;
  readonly sport: Sport | undefined;
  readonly right: ReactNode | undefined;
}

/** *Members*, and how many the list draws for the pill's sport once there is one. */
function MembersHeader({ groupId, sport, right }: MembersHeaderProps) {
  return sport === undefined ? (
    <Header title={membersTitle(undefined)} right={right} />
  ) : (
    <CountedHeader groupId={groupId} sport={sport} right={right} />
  );
}

/** The list's own query, so the title and the rows under it are one read and agree. */
function CountedHeader({ groupId, sport, right }: MembersHeaderProps & { readonly sport: Sport }) {
  const members = useGroupMembers(groupId, sport).data;
  return <Header title={membersTitle(members?.length)} right={right} />;
}

function Header({ title, right }: { readonly title: string; readonly right: ReactNode }) {
  return (
    <ScreenHeader onBack={() => router.back()} backLabel={COPY.back} title={title} right={right} />
  );
}

interface MembersListProps {
  readonly groupId: string;
  readonly sport: Sport;
  /**
   * What a refused list says, by code — `group_not_found` for a group the reader has left or no
   * longer runs. Anything else is the recovery's sentence.
   */
  readonly refused: Readonly<Record<string, string>>;
  /**
   * The group as the player's page read it, to name who runs an official group over the list
   * (`runnerApart`). Absent in the administrator area, whose reader is the one who runs it.
   */
  readonly group?: Pick<Group, 'kind' | 'administratorName' | 'isAdministrator' | 'homeClub'>;
}

function MembersList({ groupId, sport, refused, group }: MembersListProps) {
  const read = useGroupMembers(groupId, sport);
  const readerId = useReaderId();
  const members = read.data;

  /**
   * Whose record is open, or nobody's — route-local, on the players card's argument: the sheet
   * reads no global state and goes when the screen pops.
   */
  const [reading, setReading] = useState<RecordSubject>();

  // Named once the list is in, so a runner whose own row is on it is never drawn for a moment first.
  const runner =
    group === undefined || members === undefined ? undefined : runnerApart(group, members);

  return (
    <>
      <ScrollView contentContainerStyle={s.body}>
        {members === undefined ? (
          read.error === null ? null : (
            <ReadFailure
              error={read.error}
              message={codeMessage(refused, read.error)}
              onRetry={() => void read.refetch()}
            />
          )
        ) : (
          <>
            {runner === undefined ? null : <RunnerCard runner={runner} />}
            {members.length > 0 ? (
              <Card style={s.card}>
                {members.map((member, at) => {
                  const you = member.playerId === readerId;
                  return (
                    <MemberRow
                      key={member.playerId}
                      member={member}
                      sport={sport}
                      you={you}
                      divided={at > 0}
                      onOpen={() =>
                        setReading({ kind: you ? 'me' : 'player', playerId: member.playerId })
                      }
                    />
                  );
                })}
              </Card>
            ) : null}
          </>
        )}
      </ScrollView>

      {/* No `returnFocusTo`, on the players card's precedent: every row opens the same sheet, so
          there is no one control to return to. */}
      {reading === undefined ? null : (
        <PlayerRecordSheet
          visible
          onClose={() => setReading(undefined)}
          subject={reading}
          sport={sport}
        />
      )}
    </>
  );
}

/**
 * **Who runs an official group**, over the list (#529) — the club's tile, their whole nickname and the
 * admin tag, over *runs this group for Ogrody 33*; the club's name over *no administrator right
 * now* while nobody does. One element, spoken as drawn, and not a button: an Administrator need
 * not play, so there may be no record to open, and the group's read carries their name alone. Not a
 * member either, so *Members · N* does not count them.
 */
function RunnerCard({ runner }: { readonly runner: GroupRunner }) {
  return (
    <Card>
      <View
        testID="members-runner"
        style={s.row}
        accessible
        accessibilityLabel={runnerLabel(runner)}
      >
        <ClubTile clubName={runner.clubName} size="card" />
        <View style={s.words}>
          <View style={s.nameRow}>
            <Text style={s.name} numberOfLines={1}>
              {runnerName(runner)}
            </Text>
            {runner.kind === 'administrator' ? <Tag label={COPY.admin} /> : null}
          </View>
          <Text style={s.runnerLine} numberOfLines={1}>
            {runnerLine(runner)}
          </Text>
        </View>
      </View>
    </Card>
  );
}

interface MemberRowProps {
  readonly member: GroupMember;
  readonly sport: Sport;
  readonly you: boolean;
  readonly divided: boolean;
  readonly onOpen: () => void;
}

function MemberRow({ member, sport, you, divided, onOpen }: MemberRowProps) {
  const person = { ...member, you };

  return (
    <Pressable
      testID={`member-${member.playerId}`}
      accessibilityRole="button"
      accessibilityLabel={memberRowLabel(sport, person)}
      accessibilityHint={openRecordHint(person)}
      onPress={onOpen}
      hitSlop={theme.hit.peopleRow}
      // 6.6: the row is the target, so the row dims.
      style={({ pressed }) => [
        s.row,
        divided ? s.divided : undefined,
        pressed ? s.pressed : undefined,
      ]}
    >
      <PlayerPhoto
        playerId={member.playerId}
        {...(member.photoUrl === undefined ? {} : { photoUrl: member.photoUrl })}
        box={{ kind: 'face', size: ROW_FACE }}
      />
      <View style={s.words}>
        <View style={s.nameRow}>
          <Text style={s.name} numberOfLines={1}>
            {memberName(person)}
          </Text>
          <PlayerScoreTag
            score={member.playerScore}
            {...(member.reliabilityBand === undefined ? {} : { band: member.reliabilityBand })}
          />
          {adminTagged(member) ? <Tag label={COPY.admin} /> : null}
        </View>
        <View style={s.lineRow}>
          <View
            testID="member-sport-dot"
            style={[s.dot, { backgroundColor: sportColour(sport) }]}
            accessibilityElementsHidden
            importantForAccessibility="no"
          />
          <Text style={s.line} numberOfLines={1}>
            {memberLine(sport, member)}
          </Text>
        </View>
      </View>
    </Pressable>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  body: {
    paddingHorizontal: theme.size.gutter,
    paddingBottom: theme.space.lg,
    gap: theme.space.sm,
  },
  card: { gap: theme.space.sm },
  row: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  // 5.3: `line2` folds one card into rows.
  divided: {
    borderTopWidth: 1,
    borderTopColor: theme.color.line2,
    paddingTop: theme.space.sm,
  },
  pressed: { opacity: 0.7 },
  words: { flex: 1, gap: theme.space.xxs },
  nameRow: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  name: { ...theme.type.cardTitle, color: theme.color.ink, flexShrink: 1 },
  // The sport's dot, then the line — round, as every sport dot is (`SportDots`).
  lineRow: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  dot: {
    width: theme.size.sportDot,
    height: theme.size.sportDot,
    borderRadius: theme.radius.dot,
  },
  // Mono whole, as 7.19's fact line is: the Level is a figure.
  line: { ...theme.num.xs, ...theme.tabular, color: theme.color.muted, flexShrink: 1 },
  // Words, not a figure: Info's *approves joins* line.
  runnerLine: { ...theme.type.tiny, color: theme.color.muted, flexShrink: 1 },
});
