I want to include new row in the home tab to make the home complete end to end with engaging information that engages players to use the application since the very beginning.
The home a part of the Rows that currently supports it will have additional rows that can be interactive.

## 1. Scope

This work covers both frontend_player and backend. Implement the feature end to end across both projects.

## 2. Design priority

I will provide mockups that define the intended design. You have to scan and analyze all the mocks provided. These mockups take priority and must guide the final user interface.

Review the existing Architecture Decision Records (ADRs). Update an existing ADR or create a new one when necessary to document architectural decisions required by the implementation. Ensure those decisions support the provided designs in detail.
But take into account that mocks are just mocks to show you how is the design so don’t hardcode data.

## 3. Frontend implementation

For the fronted work
I will provide:

- A high-level description of the feature and its expected behavior.
- An explanation of what each screen and row does.
- Mockups defining the design and visual details of the screens, rows, and individual elements.

Use this information to infer and implement the frontend logic required across all architectural layers. Go beyond the visual layout and determine all the logic that fronted requires for every layer.

## 4. Backend implementation

For the backend work. Use the frontend description, provided mocks, and expected behavior to infer and implement the all the backend logic across all architecture layers, Database architecture and structure, Architectural decisions and design patterns where they provide clear value. Choose patterns based on the feature’s actual needs; do not force unnecessary complexity.

---

Now I will describe each row. All the rows are drawn in the order of explanation
First, I will show you how the overall screen looks like with those rows for you to know how elements are placed in the overall screen, and the sizes of the elements on the screen, how they layout. Since the home is scrollable I will provide more than one screen.

->mock reference:

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/1_home_rows_general_1.png`

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/2_homre_rows_general_2.png`

## 1-Row Hottest groups

**What it is.** The groups with the most going on, whether you’re in them or not: the ones generating the most games, holding the most players and growing fastest. Its purpose is discovery — a reason to join a second or third group rather than stay in the one you were invited to.

**How it presents.** A sideways row of up to six group cards, hottest first. A group needs at least three players to appear. The rules for hottest and growing tags are initial ideas and not final. You have to determine best option. Heat is a score built from games this week, new players this month and size; those hot cards are tagged with ▲ HOTTEST. There are also groups that are tagged with + GROWING when they not necessarily had games this week, but they gained four or more players this month is tagged. And groups that not necessarily had games this week and grow less than in four players are present but not tagged. If tagged groups Hottest and Growing fills the row completely, the groups that are not tagged are not shown. So, the row prioritizes the hottest and growing groups if enough to complete the row.
Here very important action point for you is to determine the rules for tagging a group as Hottest and growing. The rules are initial ideas and are open for optimization.

->mock reference of the row. Take into account that the last element is cut because the row is scrollable:

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/21-club_row.png`

**Each card.**

- A striped band across the top in the group’s colour, with the group’s badge overlapping it.
- The group name and its sports (colour dots plus names of the sports it supports).
- Two figures: games this week and players, the latter with a green +[n] this month when it grew.
- A heat bar filled relative to the hottest group in the row. It has to be determined if more than one hottest group can be displayed or not and therefore how the heat bar gets filled.
- A stack of up to four member faces, and the action chip: Join for an open group, Ask to join for a closed one, Asked while the admin decides, You’re in for your own groups.

**Actions.** The chip, as above — Join puts you in on the spot. Tapping the card opens the group sheet.

-.mock references of the card items for hottest groups:

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/3_hottest_groups_tile_1.png`

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/3.2_hottest_groups_tile_1.png`

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/4_hottest_groups_tile2.png`

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/5_hottest_groups_tile3.png`

**Group sheet (bottom sheet).**

- Title row: the group name, and in the top-right corner the one button — Join, Ask to join, Asked, or Open group for a group you’re in (which takes you to the group page).
- Identity row: the badge, whether the group is open or closed, who runs it, the club it plays at, and its sports that supports as dots with names.
- Two stat cards: games this week; players, with the month’s growth in green.
- People row: up to six member faces and either N of your friends play here or the player count.
  No See all screen for this row.

Obviously the data from the mocks is just mock data. SO don’t hardcode those values.

->mock reference of the bottom sheet for hottest groups tile:

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/6_hottest_groups_bottom_sheet.png`

## 2- Row Same competitive level players

**What it is.** Players whose level in a sport you both play is closest to yours — the people a competitive game with would be even. Its purpose is to answer “who should I play against?” with numbers, in any of your sports, not just the main one.

**How it presents.** A sideways row of ten cards. For each player the app looks at every sport you both play and keeps the one where the match is most even, then sorts everyone by that evenness. The row takes the first ten, so once the close matches run out it continues with players further from your level rather than stopping short. The header reads Same competitive level players with See all ›.

->mock reference of the row. Take into account that the last element is cut because the row is scrollable:: `/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/7_same_comptetitve_level_players_row.png`

**Each card (dark).**

- The pairing: your avatar, You and your level on the left; the player’s avatar, first name and level on the right.
- Between them: the balance percentage in the forecast colour, example EVEN, and the sport with its dot.
- The comparison bar on the Skill Passport scale: the four bands underneath (New · Developing · Established · Advanced, your own band in bold), the bar filled in volt up to the other player’s level, and you as a tall white mark with a YOU label — so a fill that stops short of the mark means they’re below you, and one that runs past it means they’re above.
- The footer: the gap in words (below you or above you, same level) (example: 0,03 below you), and N sports › when you share more than one sport.
- The round button which can have 3 different states:
    - add friend + button.
    - Friend Requested with the three dots (…)
    - You are Friends with green color and a check
    - The player requested you, green color with small envelope icon.

->mock references of different cards representing all the components and their states, particulary the round button:

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/8_competiive_players_card.png`

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/10_competitive_players_card2.png`

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/10.2_competitive_row_card.png`

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/10.3_competitve_card_3.png`

Since it is possible that players might share more than one sport, you have to determine hoe they are shorted by competitive level of which sport. It can be an overall computation of all the sports you both share or by sport. Is it up to you to determine the best way logic to sort the players by best competitive fit. And you have also to determine if the level of confidence should be also taken into account.

**Actions.**

- If you tap on the round button with the +, you are requesting that player to be a friend. While the request is pending the button inside will hold three dots to show the pending request status (…) with a brown color
- If you tap on the N sports › it opens the compare bottom sheet.
  ->mock references of the bottom sheet:
  `/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/9_competiive_players_bottom_sheet2.png`
  `/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/11_competitive_players_bottom_sheet2.png`
- If you tap on the see all > it navigates to the see all screen, where all the players list is visible.
- If you tap on the player profile photo square it opens the current player record.
- The round button has the same states as in the new in rakieta row tiles

**Compare sheet (bottom sheet).**

- Title row: You vs Zofia B., with the friend button in the corner as on the other sheets.
- One block per shared sport, most even first: the sport with its dot, You 2,71 · Zofia 2,69, the same comparison bar in the light theme (mint fill, ink mark), the gap in words, and a tag with the evenness (91 % even green, 51 % even amber).

Same mock references as before:
->mock references of the bottom sheet:

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/9_competiive_players_bottom_sheet2.png`

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/11_competitive_players_bottom_sheet2.png`

**See all screen — Same competitive level players.** Back arrow, title, and the sliding sport pill in the header. On All every player is shown in their most even shared sport; pick a sport and every card re-compares you in that sport, with only sports you actually share with someone offered as chips. The body is one full-width card per row, best fit first. Every card keeps its N sports › link.

->mock reference for the overall screen:

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/12_se_all_competitve_screen.png`

->mock reference that shows some cards:

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/13_se_all_competitive_card.png`

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/14_se_all_competitive_card2.png`

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/15_se_all_competitive_card3.png`

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/16_se_all_competitive_card4.png`

## 3- New in Rakieta

**What it is.** The players who joined Rakieta this month, newest first. Its purpose is to make newcomers visible on day one — before they have a ranking or a history — so existing players can add them and the deck has friends to seat them with.

**How it presents.** A sideways row of tall portrait tiles, six in the demo (Bartek 2 days ago, Michał 3 days ago, Inés on Monday, Piotr and Filip last week, Magda 2 weeks ago). The header reads New in Rakieta with See all › on the right.

->mock reference of the row. Consider that the last element is cut because the row is scrollable:

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/17_row_new_in_rakieta.png`

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/17_row_new_in_rakieta2.png`

**Each tile.**

- The player’s profile photo to the default graphic illustration fills the whole tile edge to edge, with a dark fade at the bottom.
- A volt NEW tag in the top-left corner.
- A round button in the top-right corner: + sends a friend request; it turns to … while the request is out, a green ✓ once you’re friends, and a green color with envelope icon for someone who has already asked you (tapping that accepts the friend request).
- Over the fade: the name, then every sport the player is rated in, each with its colour dot and level (example: Padel 2,44 · Tennis 2,60), and Joined 2 days ago.

->mock references of tiles:

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/18_new_players_card1.png`

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/18.2_new_players_card2.png`

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/18.3_new_players_card3.png`

**Actions.** The round button, as above. Tapping anywhere else on the tile opens the player record.

**See all screen — New in Rakieta.** Back arrow, the title, and in the header the deck’s sliding sport pill. It opens on All; the other chips are only the sports at least one newcomer plays, and picking one keeps just the players rated in it. The body is the same tiles in a two-column grid, newest first. If a sport filter leaves nobody, the grid is replaced by one line saying nobody new plays that sport yet.

->mock reference:

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/19_new_in_rakieta_screen_list.png`

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/19.2_new_in_rakieta_screen_list2.png`

## 4.Same vibe players

**What it is.** Players whose social tags overlap yours Its purpose is the other half of matchmaking: not who is your level, but who you’d enjoy a court and a coffee with.

**How it presents.** A sideways row of up to ten tiles, the players with the most tags in common first; only players sharing at least one tag qualify. The header reads Same vibe players with See all ›.

->mock references of the rows. Consider that the last element is cut because the row is scrollable:

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/20_same_vibe_row.png`

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/20.1_same_vibe_row2.png`

**Each tile.**

- A pale card tinted in the player’s own colour.
- A fit percentage in the top-right corner, rising with the number of shared tags.
- The avatar, the name, and N things in common.
- The shared tags as green chips, as many whole chips as fit in three lines; when more remain, a dashed +N more chip takes the last place.
- The round add button at bottom-right, with the same four states as the New in Rakieta tiles.

->mock references of the tiles:

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/22_same_vibe_card.png`

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/22.1_same_vibe_card1.png`

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/22.2_same_vibe_card2.png`

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/22.3_same_vibe_card3.png`

**Actions.** The round button; tapping anywhere else on the tile opens the vibe sheet.

**Vibe sheet (bottom sheet).**

- Title row: You and Karol, and in the corner the friend button — + Add friend, Request sent, ✓ Friends, or Accept if they asked first.
- Identity row: avatar, full name, N things in common · area.
- Photos: the player’s photos that he included during the onboarding as a sideways carousel of large cards, starting at the sheet’s left padding and snapping photo by photo.
- Bio: the line they wrote at onboarding, in italics.
- Tags: all of the player’s tags together; the ones you share are green and read · you too, exactly as on the player record.

->mock reference:

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/23.same_vibe_bottom_sheet.png`

**See all screen — Same vibe players.** Back arrow and title; the same tiles in a two-column grid, everyone who shares at least one tag with you, most in common first. Every tile opens the same sheet. The chip selector by sport type it is also available.

->mock reference: `/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/24.same_vibe_screen_list.png`

## 5. Top 10

**What it is.** The ten highest-ranked players of one sport, drawn from the General ranking. It gives the ranking a presence on Home — where the result that moved you was just confirmed — and shows at a glance who sits at the top.

**How it presents.** A header row with Top 10 ranked players, embedded in the header itself, the sliding sport pill (● Padel ‹) with Rankings › beside it. Under it, ten cards.

->mock reference of the row. Consider that the last element is cut because the row is scrollable:

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/25_row_top_players.png`

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/25.1_row_top_players1.png`

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/25.2_row_top_players2.png`

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/25.3_row_top_players3.png`

**Each card.**

- A huge numeral, 1 to 10, drawn in a night-to-teal gradient with a paper outline, tucked behind the left edge of the card so the card overlaps it.
- The portrait card: the player’s profile image or generated default graphic with a dark fade so that info is visible, and over it the name, the rating, and the week’s movement chip (example: ▲2, ▼1) when there is one.
- Your own card is marked: the numeral turns volt and the card gets a volt ring.

->mock references of the card. I am showing you only two example because above you have all of the cards from 1 to 10 in the row.

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/26_row_top_card.png`

`/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/26.1_row_top_card1.png`

**Dynamics.** Order and ratings come straight from the ranking by level. Tapping the sport pill slides out the other sports — only those with a ranked field of at least three players — and picking one swaps all ten cards. But only that row gets updated so there is no loading blinking on the other rows.; the row opens on your main sport.

->mock reference: `/Users/Robert.Dinescu/Desktop/rkta_dev/rakieta_v2.0/4-features/6-home_improve/27_top_players_sport_seletor.png`

**Actions.** Tap a card → the player record is shown. Tap on Rankings › → the full Rankings page for the selected sport is open. No separate See all: the Rankings page that is already built.
