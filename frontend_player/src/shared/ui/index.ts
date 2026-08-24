/**
 * The design system's primitives, as one import surface.
 *
 * Components are built with the features that need them — this barrel grows as they land,
 * and there is exactly one implementation of each. The prototype kept a second copy of
 * its card, bar and popover in a deck and recorded that they had drifted.
 */

export { Bar, type BarProps } from './Bar';
export { BottomSheet, type BottomSheetProps } from './BottomSheet';
export { Button, type ButtonProps, type ButtonSize, type ButtonVariant } from './Button';
export { Card, PressableCard, type CardProps, type PressableCardProps } from './Card';
export { CloseControl, type CloseControlProps } from './CloseControl';
export { ConfidenceRing, type ConfidenceRingProps } from './ConfidenceRing';
export { DarkCard, type DarkCardProps } from './DarkCard';
export { FitBadge, FIT_BADGE_ID, type FitBadgeProps } from './FitBadge';
export { Hairline, type HairlineProps, type HairlineVariant } from './Hairline';
export { InfoGlyph, type InfoGlyphProps } from './InfoGlyph';
export {
  LevelBar,
  type LevelBarLegend,
  type LevelBarProps,
  type LevelBarVariant,
} from './LevelBar';
export { Note, type NoteProps, type NoteVariant } from './Note';
export { InfoMark, Popover, type InfoMarkProps, type PopoverProps } from './Popover';
export { QuestionNavigator, type QuestionNavigatorProps } from './QuestionNavigator';
export { Row, type RowProps, type RowVariant } from './Row';
export {
  ScoreBoard,
  SCORE_BOARD_ROW_ID,
  type ScoreBoardProps,
  type ScoreBoardRow,
} from './ScoreBoard';
export { ScreenHeader, type ScreenHeaderProps } from './ScreenHeader';
export {
  TabBar,
  TAB_BADGE_ID,
  TAB_BAR_ID,
  TAB_CIRCLE_ID,
  tabIconId,
  tabId,
  type TabBarProps,
  type TabKey,
} from './TabBar';
export { Tag, type TagProps, type TagVariant } from './Tag';
export { behindOverlay, useReducedMotion, type FocusTarget } from './overlay';
export { theme, type BandKey, type SportKey, type Theme } from './theme';
