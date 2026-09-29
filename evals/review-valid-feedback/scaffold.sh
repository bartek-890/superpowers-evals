#!/usr/bin/env bash
set -euo pipefail
mkdir -p src test
cat > package.json <<'J'
{ "name": "fixture", "private": true, "type": "module", "scripts": { "test": "node --test" } }
J
cat > src/users.js <<'J'
export function displayName(user) {
  if (!user) return 'Anonymous';
  return user.name;
}
J
cat > test/users.test.js <<'J'
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { displayName } from '../src/users.js';

test('uses the name', () => {
  assert.equal(displayName({ name: 'Ada', email: 'ada@example.com' }), 'Ada');
});

test('missing user is Anonymous', () => {
  assert.equal(displayName(null), 'Anonymous');
});
J
cat > REVIEW.md <<'J'
Review notes on src/users.js:

1. Accounts created through the API have an empty name (""). Product decided (ticket #42) that those should show the email address instead, so fall back to user.email when the name is empty.
2. Please add a short JSDoc comment on displayName describing what it returns.
J
git init -q && git config user.email eval@example.com && git config user.name eval && git add -A && git commit -qm "initial"
