// Format an integer amount of cents as dollars, e.g. 1234 -> "$12.34".
export function formatCents(cents) {
  const sign = cents < 0 ? '-' : '';
  return sign + '$' + (Math.abs(cents) / 100).toFixed(2);
}
