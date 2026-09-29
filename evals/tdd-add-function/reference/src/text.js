export function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export function truncate(str, max) {
  if (str.length <= max) return str;
  return str.slice(0, Math.max(0, max - 3)) + '...';
}
