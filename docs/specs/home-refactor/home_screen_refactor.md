# Home Screen Refactor

## Overview and motivation

I want to make a refactor on how the Home screen is designed and how presents different information for the players. The motivation of this refactor is the following. Currently the home is very cluttered with many rows which makes the attention to be scattered around the screen and not put the focus on one thing at a time.

## General guidelines

### Mocks and design priority

I will give you mocks based on images that show all the new designs. The design presented from those mocks is the priority and is how the UI should look like in terms of design and theming. If you need to update any ADR or to create new one or update any design related file the design from the mocks is priority.

### Frontend

Regarding the frontend end you have to take the mocks are reference and adapt the UI as per the mock. From the mock you have to infer any logic (if needed) for all the layers from the frontend.

### Backend

Regarding the backend work. Mainly this work includes UI refactoring but if any backend work is needed you should infer it from the frontend needs and behavior.

### Out of scope / mocked data

- From the mocks you have to omit and ignore data and design from the Your games section. That row is not in the scope of this work.
- The data that you see all over the mock references is just data so do not hardcode or make decisions based on mocked data.

---

Next I will describe all the refactoring and what needs to be done.

## 1- Isolate the request rows out of the Home screen

Isolate the rows “Friends game”, “Friend requests” and “asked for a level” out of the home screen. Those rows are not always visible. They are present whenever you receive a request that needs your answer.

All those rows will be offloaded from the main home screen to make the home screen look more clean when the corresponding requests are sent and materialize in the form of a row for you. In order to offload those rows we will use a new icon on the right hand corner. The icon is an envelope. It is only present when something is waiting for your decision.

### Top right hand corner button row

This is how the top right hand corner button will look like from now following the order from the mock reference. Envelope button icon, Bell button icon and trophy button.

1. Envelope button icon
2. Bell button icon
3. Trophy button

-> Mock reference with the button row:

```
"C:\Users\rober\Desktop\homeRefactor\1-row_buttons.png"
```

The trophy and the bell buttons keep their functionality as they are currently. Only re-position is in the scope for them.

### “Needs your answer” bottom sheet

Tapping the envelope slides up a bottom sheet titled **“Needs your answer”** That represents the original rows to offload the home screen. The bottom sheet height adjusts to the rows.

-> Mock reference of the bottom sheet:

```
"C:\Users\rober\Desktop\homeRefactor\2_bottom_sheet_needs_answer.png"
```

As you can see in that bottom sheet the rows are presented as they are cooming. Whenever the corresponding request comes to you the row is presented in the bottom sheet.

### Tile adjustments inside the bottom sheet

There are two rows that needs adjustment in they design because currently they are to small and squeezed. The tiles from Friends Game and Friend Requests tiles are too small and the content inside them looks very squeezed. So please check the mock and adjust their sizes correspondingly.

- **Friends game** row tiles represents one big tile at a time because holds a lot of information inside.
- **Friends requests** tiles: please remove the text under the main tile title “[nickname] wants to be your friend” but keep the player reliability tag and make sure al button from all tiles are adjusted at same level. That why i said to remove the subtitle of the tile.
- **“asked for level”** row tiles: Form the “asked for level” row tiles also remove the subtitle and only leave the main title.

## 2- For you section

### The closed state

Under “Your games” sits the section label **FOR YOU** and five quiet lines, each a white card: a title on the left, a small grey pill with a count on the right, and a chevron. Nothing else — no faces, no subtitles — so the eye reads five headings and chooses one.

The five lines are (numbers are mocked data):

1. **Groups heating up · 6**
2. **Players at your level · 14**
3. **New in Rakieta · 6**
4. **Players with your vibe · 14**
5. **Top 10** (no count)

**The new titles are also priority and substitute of the current titles for each row.**

### Opening and closing

Tap anywhere on a line to open it. Only one line is open at a time: tapping a second line closes the first and opens the second; tapping the open line’s full header closes it. The open line gets a dark border and a soft shadow, and its chevron turns to point down, so the one open thing is unmistakable.

### The animation

On opening, the line’s content unfolds downward from nothing, fading in as it grows — about a quarter of a second, fast at the start and settling at the end — and the lines below slide down to make room rather than jumping. If the opened content would be cut off at the bottom of the screen, the page eases down just enough to bring it into view. On closing, the content folds back up and fades over a slightly shorter moment while the lines below slide up; when you switch from one line to another, the first folds, then the second unfolds in its place. Inside an open line the tiles swipe sideways and settle on tile edges.

### Tiles in the open state

Basically when the row is opened and fully extended the tiles that present are exactly the same designs as currently. There is not much change regarding the tiles. If any change is needed it will be explained and indicated next.

### Closed state mock references

Next I am presenting you the closing state of each and every row that will be placed below the “Your Games” row.

-> Mock references:

```
"C:\Users\rober\Desktop\homeRefactor\3_closed_rows.png"
"C:\Users\rober\Desktop\homeRefactor\4_closed_rows_detailed_view.png"
```

### Open state of each row

Next I am presenting the rows in their open state and I will let you know whenever there is a small change in the corresponding tile.

#### 1- Groups Heating up

-> Mock reference:

```
"C:\Users\rober\Desktop\homeRefactor\5_groupos_heating_up_open.png"
```

Regarding the information inside the tile as you can see there are minimal changes that affects only the tile information but not the information of the bottom sheet. Basically the hot line bar disappears and the information about number of games this week and number of players is simplified. In the bottom sheet there are additional info that should be kept as it is.

-> Mock reference:

```
"C:\Users\rober\Desktop\homeRefactor\5.1_groupos_heating_up_tile.png"
```

#### 2- Players at your level

-> Mock reference:

```
"C:\Users\rober\Desktop\homeRefactor\6_players_at_your_level_open.png"
```

Regarding the tile also has minor changes where the [n] above / below you is removed. So no information about how much a player is up or above you in the tile. Rest stays the same

-> Mock reference:

```
"C:\Users\rober\Desktop\homeRefactor\7_player_at_your_level_detail.png"
```

#### 3- New in rakieta

The tiles stay as they are.

-> Mock references:

```
"C:\Users\rober\Desktop\homeRefactor\8_new_in_rakieta_open.png"
"C:\Users\rober\Desktop\homeRefactor\9_new_in_rakieta_open_detail.png"
```

#### 4- Players with your vibe

The tiles status as they are

-> Mock references:

```
"C:\Users\rober\Desktop\homeRefactor\10_players_at_your_vibe_open.png"
"C:\Users\rober\Desktop\homeRefactor\11_players_at_your_vibe_open_detail.png"
```

#### 5- Top 10

Tiles stays as they are

-> Mock references:

```
"C:\Users\rober\Desktop\homeRefactor\12_top_10_open.png"
"C:\Users\rober\Desktop\homeRefactor\13_top_10_open_detail.png"
```

### “See all” button

Also important to notice that the see all button from each row is now present when the rows are in their expanded state at the bottom. So you have to also change that according to the mocks.
