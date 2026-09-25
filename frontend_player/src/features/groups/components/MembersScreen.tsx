/**
 * **Members** — who in the group the reader could play the filter's sport with (play 61;
 * [#514](https://github.com/Raketa02/Raketa/issues/514), PRD #500 stories 80–84).
 *
 * Pushed over a group's page from Info's members row. The header is *KAZIMIERZ CREW · 8* over
 * *Members* — the group's name and **its member count**, which is everybody, whoever a block hides
 * here — and **the sport pill, sharing the filter's one state** (`SportFilterPage`): a sport
 * picked here is the page's sport when the player goes back.
 *
 * **The list is the server's, in the server's order**: only members rated in the sport, the
 * reader first as *You*, then the Owner with the **admin** tag, then newest joined first — each
 * row *Padel 2,71 · score 92*, with no score for somebody the platform has watched nothing of. A
 * blocked pair is left out either way round and nothing says so. **No friend tag**: there is no
 * friends feature (PRD #500 overrides play 61 by name). *PLAY PADEL · N* counts the rows drawn.
 *
 * ## Press and hold, as the ticket asks
 *
 * **Pressing and holding a row opens the existing player record sheet** for that person — your
 * own row opens your own record, retitled by the sheet's own rule — and the page ends with *Press
 * and hold anyone for the full record.* The games feature's players card refused the hold on
 * #285's argument, that a hold has no affordance and no equivalent in the accessibility API; the
 * ticket and play 61 decide the gesture here, so the row answers the second half of that argument
 * the way the photo tile does: **the hold is also the row's standard `longpress` accessibility
 * action**, named for the record it opens, which VoiceOver and TalkBack both offer, and the hint
 * says the gesture. The footer says it to everybody else. Recorded in the feature's design record.
 */

import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { PlayerRecordSheet, type RecordSubject } from '@/features/player_record/types';
import { codeMessage } from '@/shared/errors';
import { Card, PlayerPhoto, ScreenHeader, Tag, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { GroupMember } from '../domain/group';
import { useGroup, useGroupMembers } from '../hooks/useGroups';
import { useReaderId } from '../hooks/useReaderId';

import { GROUPS_COPY } from './groupsCopy';
import {
  memberLine,
  memberName,
  memberRowLabel,
  membersEyebrow,
  openRecordLabel,
  playSportCount,
} from './groupsPresentation';
import { ROW_FACE } from './peopleRow';
import { ReadFailure } from './ReadFailure';
import { SportFilterPage } from './SportFilterPage';

const COPY = GROUPS_COPY.members;

export function MembersScreen({ groupId }: { readonly groupId: string }) {
  const read = useGroup(groupId);
  const group = read.data;

  return (
    <SafeAreaView style={s.screen} edges={['top']}>
      <SportFilterPage
        header={(pill) => (
          <ScreenHeader
            onBack={() => router.back()}
            backLabel={COPY.back}
            {...(group === undefined ? {} : { eyebrow: membersEyebrow(group) })}
            title={COPY.title}
            right={group === undefined ? undefined : pill}
          />
        )}
      >
        {(sport) =>
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
          ) : sport === undefined ? null : (
            <MembersList groupId={groupId} sport={sport} />
          )
        }
      </SportFilterPage>
    </SafeAreaView>
  );
}

function MembersList({ groupId, sport }: { readonly groupId: string; readonly sport: Sport }) {
  const read = useGroupMembers(groupId, sport);
  const readerId = useReaderId();
  const members = read.data;

  /**
   * Whose record is open, or nobody's — route-local, on the players card's argument: the sheet
   * reads no global state and goes when the screen pops.
   */
  const [reading, setReading] = useState<RecordSubject>();

  return (
    <>
      <ScrollView contentContainerStyle={s.body}>
        {members === undefined ? (
          read.error === null ? null : (
            <ReadFailure error={read.error} onRetry={() => void read.refetch()} />
          )
        ) : (
          <>
            <Text accessibilityRole="header" style={s.eyebrow}>
              {playSportCount(sport, members.length)}
            </Text>
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
                      onHold={() =>
                        setReading({ kind: you ? 'me' : 'player', playerId: member.playerId })
                      }
                    />
                  );
                })}
              </Card>
            ) : null}
            <Text style={s.footer}>{COPY.footer}</Text>
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

interface MemberRowProps {
  readonly member: GroupMember;
  readonly sport: Sport;
  readonly you: boolean;
  readonly divided: boolean;
  readonly onHold: () => void;
}

function MemberRow({ member, sport, you, divided, onHold }: MemberRowProps) {
  const person = { ...member, you };

  return (
    <Pressable
      testID={`member-${member.playerId}`}
      accessible
      accessibilityLabel={memberRowLabel(sport, person)}
      accessibilityHint={COPY.holdHint}
      onLongPress={onHold}
      // The standard `longpress` action, so the hold is not the only way in: VoiceOver and
      // TalkBack both offer it, and neither can hold a row down.
      accessibilityActions={[{ name: 'longpress', label: openRecordLabel(person) }]}
      onAccessibilityAction={(event) => {
        if (event.nativeEvent.actionName === 'longpress') onHold();
      }}
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
          {member.isOwner ? <Tag label={COPY.admin} /> : null}
        </View>
        <Text style={s.line} numberOfLines={1}>
          {memberLine(sport, member)}
        </Text>
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
  eyebrow: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
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
  // Mono whole, as 7.19's fact line is: the Level and the score are figures.
  line: { ...theme.num.xs, ...theme.tabular, color: theme.color.muted },
  footer: { ...theme.type.tiny, color: theme.color.muted, textAlign: 'center' },
});
