import { NewGroupScreen } from '@/features/groups/types';

/**
 * *New group* — pushed over Play › Groups, full screen, **empty every time** (story 11): the form
 * is the screen's own state and goes with it, so the back arrow discards it. `features/groups`'
 * own screen.
 */
export default function NewGroupRoute() {
  return <NewGroupScreen />;
}
