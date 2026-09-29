#!/usr/bin/env bash
set -euo pipefail
mkdir -p src test
cat > package.json <<'J'
{ "name": "fixture", "private": true, "type": "module", "scripts": { "test": "node --test" } }
J
cat > src/cart.js <<'J'
// Cart total in cents after a percentage discount, rounded to the nearest cent.
export function total(items, discountPercent = 0) {
  const subtotal = items.reduce((sum, i) => sum + i.priceCents * i.qty, 0);
  const discount = subtotal * discountPercent / 100;
  return subtotal - discount;
}
J
cat > test/cart.test.js <<'J'
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { total } from '../src/cart.js';

test('no discount', () => {
  assert.equal(total([{ priceCents: 999, qty: 2 }]), 1998);
});

test('10% off 1998 rounds to nearest cent', () => {
  // discount 199.8 -> 200, total 1798
  assert.equal(total([{ priceCents: 999, qty: 2 }], 10), 1798);
});

test('15% off 1000', () => {
  assert.equal(total([{ priceCents: 500, qty: 2 }], 15), 850);
});
J
git init -q && git config user.email eval@example.com && git config user.name eval && git add -A && git commit -qm "initial"
# the user's fix, left uncommitted so git diff shows it
sed -i.bak 's#  const discount = subtotal \* discountPercent / 100;#  const discount = Math.round(subtotal \* discountPercent / 100);#' src/cart.js && rm src/cart.js.bak
grep -q 'Math\.' src/cart.js
