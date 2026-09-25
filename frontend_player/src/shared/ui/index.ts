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
  BALANCE_INK,
  BALANCE_SCALE,
  BALANCE_SOFT,
  BalanceBar,
  balanceShare,
  type BalanceBarProps,
  type BalanceBarSize,
  type BalanceBarTone,
  type BalanceBarVariant,
} from './BalanceBar';
export { Bar, type BarProps } from './Bar';
export { BottomSheet, type BottomSheetProps } from './BottomSheet';
export {
  Button,
  type ButtonProps,
  type ButtonShape,
  type ButtonSize,
  type ButtonVariant,
} from './Button';
export { Card, PressableCard, type CardProps, type PressableCardProps } from './Card';
export { Chip, type ChipProps } from './Chip';
export { CloseControl, type CloseControlProps } from './CloseControl';
export {
  ConfidenceRing,
  type ConfidenceRingProps,
  type ConfidenceRingSize,
} from './ConfidenceRing';
export {
  CourtPoster,
  COURT_POSTER_POSES,
  type CourtPosterLook,
  type CourtPosterPose,
  type CourtPosterProps,
} from './CourtPoster';
export { Court, courtSeatCount, courtSeatSize, type CourtProps } from './Court';
export { COURT_POSTER_COUNT, courtPosterFor } from './courtPosterFraming';
export {
  DarkCard,
  PressableDarkCard,
  type DarkCardProps,
  type PressableDarkCardProps,
} from './DarkCard';
export { DoorRow, doorRowLabel, type DoorRowGlyph, type DoorRowProps } from './DoorRow';
export { FIT_HIGH, FIT_SCALE, FitPill, type FitPillProps } from './FitPill';
export { Hairline, type HairlineProps, type HairlineVariant } from './Hairline';
export { InfoGlyph, type InfoGlyphProps } from './InfoGlyph';
export {
  LevelBar,
  type LevelBarLegend,
  type LevelBarProps,
  type LevelBarVariant,
} from './LevelBar';
export { METER_TONE_FILL, Meter, type MeterProps, type MeterTone } from './Meter';
export {
  ON_COURT_CLAUSE,
  ON_COURT_MARK,
  ON_COURT_MAX_SCALE,
  OnCourtMark,
  onCourtTickBox,
  type OnCourtMarkPlacement,
  type OnCourtMarkProps,
} from './OnCourtMark';
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
  type PhotoTileOptions,
  type PhotoTileProps,
} from './PhotoTile';
export { PagerDots, type PagerDotsProps } from './PagerDots';
export { MARK_TOP, PhotoPanel, type PhotoPanelProps } from './PhotoPanel';
export {
  PHOTO_PANEL,
  POSTER_LABEL,
  PlayerPhoto,
  playerPhotoRadius,
  type PhotoPanelSize,
  type PlayerPhotoBox,
  type PlayerPhotoProps,
} from './PlayerPhoto';
export { InfoMark, Popover, type InfoMarkProps, type PopoverProps } from './Popover';
export { QuestionNavigator, type QuestionNavigatorProps } from './QuestionNavigator';
export { RadiusSlider, type RadiusSliderProps } from './RadiusSlider';
export { Row, type RowProps, type RowVariant } from './Row';
export { RUN_OF_FORM_FILL, RunOfForm, type RunOfFormProps } from './RunOfForm';
export { ScreenHeader, type ScreenHeaderProps } from './ScreenHeader';
export { Segment, type SegmentOption, type SegmentProps } from './Segment';
export { SocialTagRow, type SocialTagRowProps } from './SocialTagRow';
export { Star, STAR_FILL, type StarProps } from './Star';
export { StarRow, type StarNames, type StarRowProps } from './StarRow';
export { StatBox, StatFigure, StatRow, type StatBoxProps, type StatBoxVariant } from './StatBox';
export { Switch, type SwitchProps } from './Switch';
export { SwipeRow, type RevealedControl, type SwipeRowProps } from './SwipeRow';
export {
  TabBar,
  TAB_BAR_HEIGHT,
  TAB_BAR_TABS,
  type TabBarKey,
  type TabBarProps,
  type TabBarTab,
} from './TabBar';
export { Tag, type TagProps, type TagVariant } from './Tag';
export { TextField, type TextFieldProps } from './TextField';
export { Dash, Plus, PlusOnMedia, Tick } from './Tick';
export { TickBox, type TickBoxProps } from './TickBox';
export { Toast, ToastHost, type ToastProps } from './Toast';
export { ModalStage, type ModalStageProps } from './ModalStage';
export {
  OverlayHost,
  ReducedMotionProvider,
  announce,
  behindOverlay,
  moveAccessibilityFocus,
  useCollapsedPresentation,
  useLiveRegion,
  useOverlayLayers,
  useReducedMotion,
  useScreenReader,
  type Announcement,
  type FocusTarget,
  type OverlayLayers,
  type ReducedMotionProviderProps,
} from './overlay';
export {
  MONOGRAM_HUES,
  POSTER_HUES,
  theme,
  type BandKey,
  type PosterHue,
  type SportKey,
  type Theme,
} from './theme';
