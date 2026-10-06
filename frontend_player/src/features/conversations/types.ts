/**
 * The `conversations` feature's only public surface.
 *
 * **A booked game's room** — opened with the booking, reached from the game's details
 * ([#556](https://github.com/Raketa02/Raketa/issues/556)). The backend's messaging context arrived
 * with [#356](https://github.com/Raketa02/Raketa/issues/356), and this was the first client that
 * read it ([#363](https://github.com/Raketa02/Raketa/issues/363)).
 *
 * It was the old loop's rooms too, with the Chats tab's inbox, a plan card, quick chips and a
 * *Details* door, until that loop was removed ([#576](https://github.com/Raketa02/Raketa/issues/576)).
 * **What is exported is what has a caller**, and every caller is `features/proposals`' booked
 * game: its chat mounts the screen, its details and Home's cards find the room through the join.
 * The reads, the mappers, the words and the domain files stay internal.
 */

/**
 * **The room** — the header, the stream and the composer, handed the booking's word for the
 * header's second line by the booked game's chat that mounts it.
 */
export { ConversationScreen, type ConversationScreenProps } from './components/ConversationScreen';

/**
 * **The chat door's words, wherever it is drawn** — *"the same words as every other chat door"*.
 * A booked game's details draw one; one constant is what makes *the same words* true by
 * construction.
 */
export { OPEN_THE_CHAT } from './components/conversationPresentation';

/**
 * **A booked game's room, found by its game** (#556): a booked game's room is the reader's room
 * whose `game_id` is the game's, which is the join `GET /bookings/{id}` documents — the details'
 * *Chat* door, and whether a Home card's chat is open. It fails soft: no row is the ordinary state
 * rather than an error.
 */
export { useGameRoom, useGameRooms } from './hooks/useConversations';
