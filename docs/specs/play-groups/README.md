# Play › Groups, the club website and the Administrator: the mocks

**What PRD [#500](https://github.com/Raketa02/Raketa/issues/500) is drawn from.** These are the
product owner's mocks, copied here from `rakieta_v2.0/1-play` (62 mocks) and `rakieta_v2.0/club` (19
mocks, numbered 1–11 and 13–20, with no 12) so that every session can read them. Landed by
[#501](https://github.com/Raketa02/Raketa/issues/501) on 2026-09-25.

## How to read them

1. **The mocks come first.** Where a mock and a sentence disagree, the mock wins, unless PRD #500,
   an ADR or a ticket overrides it **by name**. Every override known today is listed under
   [*Overrides*](#overrides), and nothing here overrides silently.
2. **The decisions live elsewhere.** The domain is decided by seven records:
   - [ADR-0182](../../adr/0182-a-club-is-a-place-players-search-and-its-account-signs-in-only-on-the-club-surface.md): clubs
   - [ADR-0183](../../adr/0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md): groups
   - [ADR-0184](../../adr/0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md): administrators and one-time credentials
   - [ADR-0185](../../adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md): one account, several profiles
   - [ADR-0186](../../adr/0186-email-goes-through-a-port-and-a-purged-queue.md): email
   - [ADR-0187](../../adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md): the two web apps
   - [ADR-0188](../../adr/0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md): remembering on the phone

   The words are in the root [`CONTEXT.md`](../../../CONTEXT.md), under **Club**, **Groups** and
   **Administrators**. The product owner's feature document (`rkta_play_club_administrator.md`)
   isn't copied: PRD #500 restates it with the grilled rulings applied, and it's the text to cite.
3. **Cite a mock by folder and number**: *play 14*, *club 20*. The numbers are the product owner's.
   The file names were only cleaned of typos (`grops`, `freinds`, `administratpr`, and so on) and
   zero-padded so they sort. The [index](#index) gives each original name.
4. **The mocks say *Rakieta* and show `rakieta.app/g/…` links.** The name is the brand as written
   (ADR-0211). The link is illustrative: a group link is the configured public site address
   followed by `/join/<8-character code>` (ADR-0183 §4).

## Which mocks draw which area

| Area | Mocks | Built by |
| --- | --- | --- |
| Play: the Groups entry and the list | play [1](mocks/play/01_groups_entry_point_screen.png), [3](mocks/play/03_groups_explore_tabs.png), [38](mocks/play/38_group_list_card.png) | [#512](https://github.com/Raketa02/Raketa/issues/512) |
| New group | play [4](mocks/play/04_new_group_screen.png)–[13](mocks/play/13_new_group_button.png). The home club is **required**, overriding play 4 | [#512](https://github.com/Raketa02/Raketa/issues/512) |
| Join a group | play [23](mocks/play/23_join_group_empty_state.png)–[37](mocks/play/37_join_group_result_card_4.png) | [#512](https://github.com/Raketa02/Raketa/issues/512) |
| The group page: header, fast filter, tab bar, Games | play [14](mocks/play/14_new_group_page_games_tennis.png)–[17](mocks/play/17_new_group_game_badminton.png), [39](mocks/play/39_group_page_general.png)–[43](mocks/play/43_group_page_tab_bar.png) | [#513](https://github.com/Raketa02/Raketa/issues/513) |
| Fill in | play [45](mocks/play/45_group_page_fill_in.png)–[47](mocks/play/47_group_page_fill_in_post_a_game_button.png) | [#513](https://github.com/Raketa02/Raketa/issues/513) |
| Friends: the court and the Friends screen | play [49](mocks/play/49_group_page_friends_general.png)–[55](mocks/play/55_group_page_friends_screen_empty_message.png): the empty court in each sport and the empty picker. **Friends itself** — seating friends, the card, sending, requests — is drawn by the twelve mocks of [the Friends spec set](../friends/README.md) (PRD [#743](https://github.com/Raketa02/Raketa/issues/743)) | [#513](https://github.com/Raketa02/Raketa/issues/513); with friends, [#757](https://github.com/Raketa02/Raketa/issues/757) |
| Info, the group's own screen, opened from the group page's header (Q125, [*Overrides*](#overrides)) | play [57](mocks/play/57_group_page_info_initial.png)–[60](mocks/play/60_group_page_info_cards_initial.png) | [#514](https://github.com/Raketa02/Raketa/issues/514); its own screen, [#721](https://github.com/Raketa02/Raketa/issues/721) |
| Members | play [61](mocks/play/61_members_page.png) | [#514](https://github.com/Raketa02/Raketa/issues/514) |
| The request card, **everywhere** | club [20](mocks/club/20_request_to_join_card.png), replacing play 62 | [#514](https://github.com/Raketa02/Raketa/issues/514), [#516](https://github.com/Raketa02/Raketa/issues/516) |
| The club website: sign in, Administrators, Groups | club [1](mocks/club/01_club_sign_in.png)–[4](mocks/club/04_club_admin_invitation_sent.png), [14](mocks/club/14_administrator_table.png)–[16](mocks/club/16_groups_club_table.png) | [#522](https://github.com/Raketa02/Raketa/issues/522)–[#524](https://github.com/Raketa02/Raketa/issues/524) |
| The invitation sheet and the profile switcher | club [5](mocks/club/05_player_admin_invitation.png)–[7](mocks/club/07_profile_selector_player_admin.png) | [#518](https://github.com/Raketa02/Raketa/issues/518) |
| The Administrator's side of the app | club [8](mocks/club/08_administrator_view_general_no_groups_yet.png)–[11](mocks/club/11_administrator_group_created.png), [13](mocks/club/13_administrator_group_created_details.png), [17](mocks/club/17_administrator_with_groups_in_filled.png)–[19](mocks/club/19_administrator_group_no_pending_request.png) | [#516](https://github.com/Raketa02/Raketa/issues/516), [#517](https://github.com/Raketa02/Raketa/issues/517) |
| A group seen from outside it: the card, the group sheet and Withdraw (2026-11-14) | home rows 3–6 and 21, in [the Home rows spec set](../home-rows/README.md#index) | [#792](https://github.com/Raketa02/Raketa/issues/792), [#800](https://github.com/Raketa02/Raketa/issues/800) |

**Mocks exist for none of these:** the sign-up page and Club details on the club website, the public
site, the app's *Set your password*, *Have an invitation code?*, *Forgot password* and *Set a new
password* screens, Edit group, and the Administrator's You tab. The club website's sign-up follows
club 1's look. The public site borrows the club website's look (paper, the coral square wordmark, a
white card) and is laid out for phones first. The app's account screens are built from the sign-in
screen's own components.

> **Amended 2026-11-14** by [ADR-0204](../../adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md)
> §3 (the games and fill-in mechanics Q131, PRD [#789](https://github.com/Raketa02/Raketa/issues/789)):
>
> - **A non-member sees a group from outside**, on Home's *Hottest groups*: its card and **the group
>   sheet** — the name, *Open group* or *Closed group*, *run by* the club or the Owner's nickname, the
>   club, the sports, *games this week*, *players · new this month*, up to six member faces that can't
>   be tapped, and *7 of your friends play here* or *11 players* — with **Join**, **Ask to join**,
>   **Asked** or, for a member, **Open group** ([the home rows screens §3](../home-rows/the-screens.md#3-hottest-groups)).
>   **The group page itself stays members-only.**
> - **A Join request can be withdrawn**: *Asked* opens *Waiting for Ogrody 33 to answer* with
>   **Withdraw request**. It leaves the Owner's, the Administrator's and the club website's request
>   lists at once, tells nobody, and the player may ask again
>   ([the home rows mechanics §5.8](../home-rows/the-mechanics.md#58-withdrawing-a-join-request-q12)).

## Background only

**Play [2](mocks/play/02_explore_tab_general.png), [18](mocks/play/18_new_group_fill_in.png)–[22](mocks/play/22_group_info.png),
[44](mocks/play/44_group_page_games_representation.png), [48](mocks/play/48_group_page_fill_in_normal_state.png)
and [56](mocks/play/56_group_page_friends_complete.png) are background only.** Read them to understand
where the feature is going, and build nothing from them. They show things that are out of scope:

- Explore's contents
- a picked game with *Book it now* and a price
- count badges on the group's tabs
- a completed friends court
- earlier drafts of the group page, which play 39–61 replace

Play 56's completed friends court is now in scope (PRD [#743](https://github.com/Raketa02/Raketa/issues/743)),
and *friends 7–8* in [the Friends spec set](../friends/README.md) draw it and lead; play 56 stays
background.

## Overrides

Each of these is a ruling in PRD #500, a later decision, or their tickets. The mock is correct
everywhere else.

| Mock | What it draws | What is built |
| --- | --- | --- |
| play 4 | *HOME CLUB · optional*, and *"with no home club the app looks at every court within 6 km"* | **The home club is required.** *Create the group* stays disabled until there is a name and a home club, and the line under the field is the one from play 11 onwards. |
| play 62 | the owner's request card: short sport names, a *score*, and *No* / *Approve* | **Club 20's card, everywhere**, for owners and administrators alike: full sport names with each Level (*Padel 2,44 · Tennis 2,60*), no Player Score, **✕** and **Approve**. |
| club 11, 13, 18 | club 18's link card with a *posted 40 d ago* tag and *Post again* | **Club 11's card, always**: *"Post this in the WhatsApp group. Everybody who taps it lands here."*, **Post to WhatsApp** and **Copy link**. There is no *posted* tag and no *Post again* state. |
| club 8, 9 | the Administrator's Groups tab headed by the person's name, with the profile switcher chip | **Club 17's header**: *OGRODY 33 · ADMINISTRATOR / Groups*. The switcher chip sits **on the You tab only**, in both profiles (club 7; ADR-0185 §3). Club 8–9's button and empty card stand. |
| every play mock | a three-tab bar: Games · Play · You | **The bar is Home · ⚡ Play · You** (#576); the five-tab bar went with Classic play. The Administrator's side has its own two tabs, **Groups · You** (club 17–19). |
| club 15, 16 | *Games* of 8 and 9. The feature document beside them also says *Players* excludes the administrator and the rows aren't tappable | ***Games* counts the games booked in the group** — every game its deck filled into a booking, never one two of its members arranged elsewhere (ADR-0183 §11, amended by ADR-0189). *Players* is **the group's member count**, including an Administrator who joined as a player. **Every row is tappable** and opens the Hand over page (#500 story 108, [#524](https://github.com/Raketa02/Raketa/issues/524)), where any official group can be handed over (ADR-0183 §8). |
| the group page: play 14–17, 39–60 and 62, and the games-and-fill-in mocks [1](../games-and-fill-in/mocks/player/1-games_tap_general_view.png), [9](../games-and-fill-in/mocks/player/9_competitive_forfun_tap.png) and [11](../games-and-fill-in/mocks/player/11_fill_in_tap_general.png) | a tab bar of four, *Games · Fill in · Friends · Info* (play 43, and every mock that shows the bar); Info's content on that fourth tab (play 57–60, 62); and a header that is not a button | **Three tabs: Games · Fill in · Friends.** **Info opens from the header** as its own screen, with the same content: the group's monogram, its name with the official mark and *N members · home club* are one button. **The Owner's count of waiting requests is on the monogram's corner.** The rest is Q125 in the [games-and-fill-in decision log](../games-and-fill-in/the-mechanics.md#appendix-c--decision-log). |
| every mock | *Rakieta*, `rakieta.app/g/…` | **Rakieta**, as drawn (ADR-0211), and `<public site>/join/<code>`. |

## Index

### `mocks/play/`

| # | File | Original name |
| --- | --- | --- |
| 1 | `01_groups_entry_point_screen.png` | `1-groups_entry_point_screen.png.png` |
| 2 | `02_explore_tab_general.png` *(background)* | `2_explore_tab_general.png` |
| 3 | `03_groups_explore_tabs.png` | `3_grops_explore_tabs.png` |
| 4 | `04_new_group_screen.png` *(overridden: home club required)* | `4_new_group_screen.png` |
| 5 | `05_new_group_header_name_card.png` | `5_new_group_header_name_card.png` |
| 6 | `06_new_group_home_club_empty_state.png` | `6_new_group_home_club_empty_state.png` |
| 7 | `07_new_group_home_club_searching_state_1.png` | `7_new_group_home_club_seraching_state1.png` |
| 8 | `08_new_group_searching_state_2.png` | `8_new_group_searching_state_2.png` |
| 9 | `09_new_group_searching_ask_to_join.png` | `9_new_group_searching_ask_to_join.png` |
| 10 | `10_new_group_searching_after_press_ask_to_join.png` | `10_new_group_searching_after_press_ask_to_join.png` |
| 11 | `11_new_group_searching_selected.png` | `11_new_group_searching_selected.png` |
| 12 | `12_new_group_who_can_join_card.png` | `12_new_group_who_can_join_card.png` |
| 13 | `13_new_group_button.png` | `13_new_group_button.png` |
| 14 | `14_new_group_page_games_tennis.png` | `14_new_group_page_games_tennis.png` |
| 15 | `15_new_group_games_padel.png` | `15_new_group_games_padel.png` |
| 16 | `16_new_group_games_squash.png` | `16_new_group_games_squash.png` |
| 17 | `17_new_group_game_badminton.png` | `17_new_group_game_badminton.png` |
| 18 | `18_new_group_fill_in.png` *(background)* | `18_new_group_fill_in.png` |
| 19 | `19_new_group_friends.png` *(background)* | `19_new_group_friends.png` |
| 20 | `20_new_group_plus_friends.png` *(background)* | `20_new_group_+_friends.png` |
| 21 | `21_new_group_info.png` *(background)* | `21_new_group_info.png` |
| 22 | `22_group_info.png` *(background)* | `22_groun_info.png` |
| 23 | `23_join_group_empty_state.png` | `23_join_group_empty_state.png` |
| 24 | `24_join_group_searching_state.png` | `24_join_group_searching_state.png` |
| 25 | `25_join_group_header.png` | `25_join_group_header.png` |
| 26 | `26_join_group_search_bar_typing.png` | `26_join_group_search_bar_typing.png` |
| 27 | `27_join_group_link_paste.png` | `27_join_group_link_paste.png` |
| 28 | `28_join_group_link_paste_2.png` | `28_join_group_link_paste.png` |
| 29 | `29_join_group_nothing_matches.png` | `29_join_group_nothing_matches.png` |
| 30 | `30_join_group_search_by_link.png` | `30_join_group_search_by_link.png` |
| 31 | `31_join_group_search_by_group_name.png` | `31_join_group_search_by_group_name.png` |
| 32 | `32_join_group_search_by_club.png` | `32_join_group_search_by_club.png` |
| 33 | `33_join_group_search_by_club_2.png` | `33_join_group_search_by_club.png` |
| 34 | `34_join_group_result_card_1.png` | `34_join_grup_result_card1.png` |
| 35 | `35_join_group_result_card_2.png` | `35_join_group_result_card2.png` |
| 36 | `36_join_group_result_card_3.png` | `36_join_group_result_card3.png` |
| 37 | `37_join_group_result_card_4.png` | `37_join_group_result_card4.png` |
| 38 | `38_group_list_card.png` | `38_group_list_card.png` |
| 39 | `39_group_page_general.png` | `39_group_page_general.png` |
| 40 | `40_group_page_header.png` | `40_group_page_header.png` |
| 41 | `41_fast_filter.png` | `41_fast_filter.png` |
| 42 | `42_fast_filter_unfolded.png` | `42_fast_filter_unfolded.png` |
| 43 | `43_group_page_tab_bar.png` | `43_group_page_tab_bar.png` |
| 44 | `44_group_page_games_representation.png` *(background)* | `44_group_page_games_representation.png` |
| 45 | `45_group_page_fill_in.png` | `45_group_page_fill_in.png` |
| 46 | `46_group_page_fill_in_with_button.png` | `46_group_page_fill_in_with_button.png` |
| 47 | `47_group_page_fill_in_post_a_game_button.png` | `47_group_page_fill_in_postagame_button.png` |
| 48 | `48_group_page_fill_in_normal_state.png` *(background)* | `48_group_page_fill_in_normal_state.png` |
| 49 | `49_group_page_friends_general.png` | `49_group_page_friends_general.png` |
| 50 | `50_group_page_padel_court.png` | `50_group_page_padel_court.png` |
| 51 | `51_group_page_friends_tennis_court.png` | `51_group_page_friends_tennis_court.png` |
| 52 | `52_group_page_friends_squash_court.png` | `52_group_page_freinds_squash_court.png` |
| 53 | `53_group_page_friends_badminton_court.png` | `53_group_page_friends_badminton_court.png` |
| 54 | `54_group_page_friends_screen_initial_state.png` | `54_group_page_friends_screen_initial_state.png` |
| 55 | `55_group_page_friends_screen_empty_message.png` | `55_group_page_friends_screen_empty_message.png` |
| 56 | `56_group_page_friends_complete.png` *(background)* | `56_group_page_freinds_complete.png` |
| 57 | `57_group_page_info_initial.png` | `57_group_page_info_initial.png` |
| 58 | `58_groups_page_info_filled.png` | `58_groups_page_info_filled.png` |
| 59 | `59_groups_page_info_cards_group_filled.png` | `59_groups_page_info_cards_group_filled.png` |
| 60 | `60_group_page_info_cards_initial.png` | `60_group_page_info_cards_initial.png` |
| 61 | `61_members_page.png` | `61_members_page.png` |
| 62 | `62_group_page_info_request.png` *(replaced by club 20)* | `62_group_page_info_reqeust.png` |

### `mocks/club/`

| # | File | Original name |
| --- | --- | --- |
| 1 | `01_club_sign_in.png` | `1-club_sign_in.png` |
| 2 | `02_club_administrator_tab_general.png` | `2_club_administrator_tab_general.png` |
| 3 | `03_club_administrator_tab_add_administrator.png` | `3_club_administrator_tab_add_administrator.png` |
| 4 | `04_club_admin_invitation_sent.png` | `4_club_admin_invitation_sent.png` |
| 5 | `05_player_admin_invitation.png` | `5_player_admin_invitation.png` |
| 6 | `06_player_admin_invitation_accept.png` | `6_player_admin_invitation_accept.png` |
| 7 | `07_profile_selector_player_admin.png` | `7_profile_selector_player_admin.png` |
| 8 | `08_administrator_view_general_no_groups_yet.png` *(header overridden by 17)* | `8_administrator_view_general_no_groups_yet.png` |
| 9 | `09_administrator_view_detailed_no_groups_yet.png` *(header overridden by 17)* | `9_administratorview_detailed_no_groups_yet.png` |
| 10 | `10_administrator_new_official_group.png` | `10_administratpr_new_official_group.png` |
| 11 | `11_administrator_group_created.png` *(the link card, always)* | `11_administrtor_group_created.png` |
| 13 | `13_administrator_group_created_details.png` | `13_administrator_group_created_details.png` |
| 14 | `14_administrator_table.png` | `14_administrator_table.png` |
| 15 | `15_groups_club.png` | `15_groups_club.png` |
| 16 | `16_groups_club_table.png` | `16_groups_club_table.png` |
| 17 | `17_administrator_with_groups_in_filled.png` | `17_administrator_with_groups_in_filled.png` |
| 18 | `18_administrator_group_page.png` *(its link card overridden by 11)* | `18_administrator_group_page.png` |
| 19 | `19_administrator_group_no_pending_request.png` | `19_administrator_group_no_pending_request.png` |
| 20 | `20_request_to_join_card.png` *(the request card, everywhere)* | `20_requet_to_join_card.png` |
