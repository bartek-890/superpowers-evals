// Cart total in cents after a percentage discount, rounded to the nearest cent.
export function total(items, discountPercent = 0) {
  const subtotal = items.reduce((sum, i) => sum + i.priceCents * i.qty, 0);
  const discount = Math.round(subtotal * discountPercent / 100);
  return subtotal - discount;
}
