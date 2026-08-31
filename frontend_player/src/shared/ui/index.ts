/**
 * The design system's primitives, as one import surface.
 *
 * Components are built with the features that need them — this barrel grows as they land,
 * and there is exactly one implementation of each. The prototype kept a second copy of
 * its card, bar and popover in a deck and recorded that they had drifted.
 */

export {
  AvailabilityGrid,
  type AvailabilityDiffCell,
  type AvailabilityDiffRow,
  type AvailabilityDiffState,
  type AvailabilityGridCell,
  type AvailabilityGridDiffProps,
  type AvailabilityGridEditorProps,
  type AvailabilityGridProps,
  type AvailabilityGridRow,
} from './AvailabilityGrid';
export {
  BALANCE_SCALE,
  BalanceBar,
  balanceShare,
  type BalanceBarProps,
  type BalanceBarSize,
  type BalanceBarTone,
  type BalanceBarVariant,
} from './BalanceBar';
export { Bar, type BarProps } from './Bar';
export { BottomSheet, type BottomSheetProps } from './BottomSheet';
export { Button, type ButtonProps, type ButtonSize, type ButtonVariant } from './Button';
export { Card, PressableCard, type CardProps, type PressableCardProps } from './Card';
export { Chip, type ChipProps } from './Chip';
export { CloseControl, type CloseControlProps } from './CloseControl';
export { ConfidenceRing, type ConfidenceRingProps } from './ConfidenceRing';
export {
  CourtPoster,
  COURT_POSTER_POSES,
  type CourtPosterLook,
  type CourtPosterPose,
  type CourtPosterProps,
} from './CourtPoster';
export { Court, courtSeatCount, courtSeatSize, type CourtProps } from './Court';
export { DarkCard, type DarkCardProps } from './DarkCard';
export { FIT_HIGH, FIT_SCALE, FitPill, type FitPillProps } from './FitPill';
export { Hairline, type HairlineProps, type HairlineVariant } from './Hairline';
export { InfoGlyph, type InfoGlyphProps } from './InfoGlyph';
export {
  LevelBar,
  type LevelBarLegend,
  type LevelBarProps,
  type LevelBarVariant,
} from './LevelBar';
export { Note, type NoteProps, type NoteVariant } from './Note';
export {
  PhotoAddTile,
  PhotoPosterTile,
  PhotoRow,
  PhotoTile,
  type PhotoAddTileProps,
  type PhotoPosterTileProps,
  type PhotoRowProps,
  type PhotoTileFoot,
  type PhotoTileProps,
} from './PhotoTile';
export { InfoMark, Popover, type InfoMarkProps, type PopoverProps } from './Popover';
export { QuestionNavigator, type QuestionNavigatorProps } from './QuestionNavigator';
export { RadiusSlider, type RadiusSliderProps } from './RadiusSlider';
export { Row, type RowProps, type RowVariant } from './Row';
export { ScreenHeader, type ScreenHeaderProps } from './ScreenHeader';
export { Switch, type SwitchProps } from './Switch';
export {
  TabBar,
  TAB_BAR_HEIGHT,
  TAB_BAR_TABS,
  type TabBarKey,
  type TabBarProps,
  type TabBarTab,
} from './TabBar';
export { Tag, type TagProps, type TagVariant } from './Tag';
export { Dash, Plus, Tick } from './Tick';
export { TickBox, type TickBoxProps } from './TickBox';
export { Toast, ToastHost, type ToastProps } from './Toast';
export {
  announce,
  behindOverlay,
  useReducedMotion,
  type Announcement,
  type FocusTarget,
} from './overlay';
export {
  POSTER_HUES,
  theme,
  type BandKey,
  type PosterHue,
  type SportKey,
  type Theme,
} from './theme';
