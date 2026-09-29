#!/usr/bin/env bash
set -euo pipefail
mkdir -p src test
cat > package.json <<'J'
{ "name": "fixture", "private": true, "type": "module", "scripts": { "test": "node --test" } }
J
cat > src/money.js <<'J'
// Format an integer amount of cents as dollars, e.g. 1234 -> "$12.34".
export function formatCents(cents) {
  return '$' + (cents / 100).toFixed(2);
}
J
cat > test/money.test.js <<'J'
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { formatCents } from '../src/money.js';

test('formats positive amounts', () => {
  assert.equal(formatCents(1234), '$12.34');
  assert.equal(formatCents(5), '$0.05');
});
J
git init -q && git config user.email eval@example.com && git config user.name eval && git add -A && git commit -qm "initial"
