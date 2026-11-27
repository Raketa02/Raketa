I want to remove the sub taps (competitive and for fun) and make the parent tabs Games and Friends to be the holders of a small menu with both options competitive and for fun.

### The idea in one line

Inside a group there are four tabs — Games · Fill in · You're in · Friends. Two of them, Games and Friends, have a second layer: the kind of game, Competitive or For fun. That choice currently lives in its own row under the tabs, on screen all the time.This makes the screen to not look as clean as possible. The main idea is to move that second layer of tabs to live inside the tab itself (Games and Friends): you get to it by tapping the tab you're already on. The row is gone and the card below gets the room.

### What you see

**When you're on another tab** — say Fill in — Games and Friends look exactly like the other tabs: a label, and a red count if there's something to see. Nothing hints at the second layer, because you don't need it yet.

**When you're on Games (or Friends)** — the tab turns white as always, and a small chevron appears at its right edge, pointing down. That chevron is the whole signal: *this tab has more in it.* It's quiet enough not to compete with the counts, visible enough that you notice it the first time you land here. Fill in and You're in never show one, because they have no second layer.

->mock references of Games and Friends tap when are just selected:

"C:\Users\rober\Desktop\rakieta_features\5.club_tab\1.games_tab_with_chevron.png"

"C:\Users\rober\Desktop\rakieta_features\5.club_tab\2.friends_tab_with_chevron.png"

**When the menu is open** — the chevron flips to point up, and a small white menu hangs from the bottom of the tab, as if it had folded out of it. Two lines: **Competitive** and **For fun**. The one you're currently in has a red tick in front of it. In Games, each line also shows how many cards are waiting in that deck as currently (this is already implemented) so you know what you'd be switching to before you switch. In Friends there are no counts, because there's nothing to count: it's just the kind of game you're about to set up. Take into account that now the card to select “Either suits me”, “For fun”, “Competitve” when you have only a single intent defined for that sport will appear as currently does when eligible and switching the the competitive or for fun option from the small tab menu.

-> mock references when the tabs are clicked for the second time:

"C:\Users\rober\Desktop\rakieta_features\5.club_tab\3_games_tap_menu_open.png"

"C:\Users\rober\Desktop\rakieta_features\5.club_tab\4_friends_tap_menu_open.png"

### What each tap does

- **Tap a tab you're not on** → you go there. Same as it has always been, and the menu, if it was open, goes away.
- **Tap the tab you're on (Games or Friends)** → the menu opens. Nothing else moves; the deck stays where it is.
- **Tap the tab again, or tap anywhere else on the screen** → the menu closes. No choice made, nothing changed.
- **Pick the other mode** → the menu folds away and the content changes under it:
  - in **Games**, the deck is swapped in place. The competitive cards slide out and the For-fun cards rise into the same spot, with the For-fun top card ready to swipe. You stay on Games; nothing scrolls, nothing navigates. If changing between competitive and for fun the deck needs to load, a loading indicator is visible. Evaluate the best options to make the change between competitive and improve the switch to be smoother to provide better user experience.
  - in **Friends**, the court you're building on becomes a Competitive or a For-fun game.
- **Pick the mode you're already in** → the menu just closes.

### Why it's built this way

- **It's a setting, not a filter you use every minute.** Most players pick a mode once and stay in it for weeks. Giving it a permanent row meant more space of every Games and Friends screen spent on something tapped rarely; folding it into the tab costs those players nothing and gives the deck card the height it needed so the deck get the remaining available space so that all the elements inside are better visible.
- **The second tap is discoverable but never in the way.** A tab you're on has no other job — tapping it again did nothing before — so the gesture is free. The chevron tells you it's there; the flip and the drop confirm that you did the right thing.
- **You see before you choose.** The counts in the Games menu answer the only question that matters before switching ("is there anything on the other side?"), so nobody switches into an empty deck by surprise. This is already implemented and its logic stays. Only different design from the mock is the tiny change.
