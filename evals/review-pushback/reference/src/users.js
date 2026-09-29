/** Returns the user's trimmed name, or "Anonymous" when there is no user or name (e.g. deleted accounts). */
export function displayName(user) {
  if (!user || !user.name) return 'Anonymous';
  return user.name.trim();
}
