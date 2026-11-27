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
  BALANCE_FIGURE,
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
export {
  BottomSheet,
  SHEET_LIST,
  type BottomSheetProps,
  type SheetLayoutTransition,
} from './BottomSheet';
export {
  Button,
  type ButtonMark,
  type ButtonProps,
  type ButtonShape,
  type ButtonSize,
  type ButtonVariant,
} from './Button';
export { Card, PressableCard, type CardProps, type PressableCardProps } from './Card';
export { Chip, type ChipProps } from './Chip';
export { ComparisonBar, type ComparisonBarProps, type ComparisonBarVariant } from './ComparisonBar';
export { CloseControl, type CloseControlProps } from './CloseControl';
export { CornerBadge, type CornerBadgeProps } from './CornerBadge';
export { CountBadge, type CountBadgeProps, type CountBadgeTone } from './CountBadge';
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
export {
  FoldingLine,
  FoldingLineFooter,
  FoldingLines,
  type FoldingLineFooterProps,
  type FoldingLineLink,
  type FoldingLineParts,
  type FoldingLineProps,
  type FoldingLinesProps,
} from './FoldingLine';
export { ForecastBlock, type ForecastBlockProps } from './ForecastBlock';
export { Guide, type GuideProps, type GuideStep } from './Guide';
export { Hairline, type HairlineProps, type HairlineVariant } from './Hairline';
export {
  HomeRow,
  HomeRowRail,
  type HomeRowProps,
  type HomeRowRailGeometry,
  type HomeRowRailProps,
} from './HomeRow';
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
  PageOnScreen,
  PageReveal,
  scrollToReveal,
  useWatchedPage,
  type Followed,
  type Span,
  type WatchedPage,
} from './onScreen';
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
export { PhotoCarousel, type CarouselPhoto, type PhotoCarouselProps } from './PhotoCarousel';
export { PortraitTile, type PortraitTileProps } from './PortraitTile';
export { TINTED_TILE, TintedTile, type TintedTileProps } from './TintedTile';
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
export { Reveal, useRevealParts, type PartsRevealed, type RevealProps } from './Reveal';
export { REVEAL_CEILING } from './revealParts';
export { Row, type RowProps, type RowVariant } from './Row';
export { RowSportPill, type RowSportPillProps } from './RowSportPill';
export { RUN_OF_FORM_FILL, RunOfForm, type RunOfFormProps } from './RunOfForm';
export { ScreenHeader, type ScreenHeaderProps } from './ScreenHeader';
export {
  SEAT_NAME_LETTERS,
  SeatCaption,
  SeatFace,
  seatBox,
  seatCaptionName,
  type CourtFaceOccupant,
  type SeatCaptionProps,
  type SeatFaceProps,
} from './SeatFace';
export { Segment, type SegmentMenu, type SegmentOption, type SegmentProps } from './Segment';
export {
  SkeletonBlock,
  SkeletonCircle,
  SkeletonGround,
  SkeletonLine,
  SkeletonWords,
  type SkeletonBlockProps,
  type SkeletonCircleProps,
  type SkeletonGroundProps,
  type SkeletonLineProps,
  type SkeletonWordsProps,
} from './Skeleton';
export { SocialTagRow, type SocialTagRowProps } from './SocialTagRow';
export {
  SOCIAL_VIBE_CARD,
  SOCIAL_VIBE_CARD_FIGURE,
  SOCIAL_VIBE_CARD_FILL,
  SocialVibeCard,
  type SocialVibeCardProps,
} from './SocialVibeCard';
export { SOCIAL_VIBE_ON_DARK, SocialVibeRow, type SocialVibeRowProps } from './SocialVibeRow';
export {
  ALL_SPORTS,
  SportPillFrame,
  type AnotherSport,
  type SportChoice,
  type SportPillFrameProps,
  type SportPillWords,
} from './SportPillFrame';
export { Star, STAR_FILL, type StarProps } from './Star';
export { StarRow, type StarNames, type StarRowProps } from './StarRow';
export { StakeTiles, type StakeTilesProps } from './StakeTiles';
export { StatBox, StatFigure, StatRow, type StatBoxProps, type StatBoxVariant } from './StatBox';
export { Switch, type SwitchProps } from './Switch';
export { SwipeRow, type RevealedControl, type SwipeRowProps } from './SwipeRow';
export {
  ADMINISTRATOR_TAB_BAR_TABS,
  AdministratorTabBar,
  TabBar,
  TAB_BAR_MARKER_TEST_ID,
  TAB_BAR_TABS,
  TAB_BAR_TEST_ID,
  type AdministratorTabBarKey,
  type AdministratorTabBarProps,
  type TabBarKey,
  type TabBarProps,
  type TabBarTab,
} from './TabBar';
export {
  useFullTabBarReach,
  useRoomAtTheBottom,
  useSaysTabBarReach,
  useTabBarReach,
} from './tabBarReach';
export {
  TabMenu,
  type MenuAlign,
  type MenuFrame,
  type TabMenuLine,
  type TabMenuProps,
} from './TabMenu';
export { TAG_HEIGHT, Tag, type TagProps, type TagVariant } from './Tag';
export { TextField, type TextFieldProps } from './TextField';
export { TopSafeArea, type TopSafeAreaProps } from './TopSafeArea';
export { Dash, Plus, PlusOnMedia, PlusOnSurface, Tick, TICK_PATH, TICK_SPACE } from './Tick';
export { TickBox, type TickBoxProps } from './TickBox';
export { Toast, ToastHost, type ToastProps } from './Toast';
export { UndoToast, type UndoToastProps } from './UndoToast';
export { ModalStage, type ModalStageProps } from './ModalStage';
export {
  OverlayHost,
  ReducedMotionProvider,
  SplashCoverProvider,
  announce,
  behindOverlay,
  moveAccessibilityFocus,
  useCollapsedPresentation,
  useCoveredBySplash,
  useLiveRegion,
  useOverlayLayers,
  useReducedMotion,
  useScreenReader,
  type Announcement,
  type FocusTarget,
  type OverlayLayers,
  type ReducedMotionProviderProps,
  type SplashCoverProviderProps,
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
