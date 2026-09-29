/** Returns the name to show for a user: their name, their email if the name is empty, or "Anonymous" if there is no user. */
export function displayName(user) {
  if (!user) return 'Anonymous';
  return user.name || user.email;
}
