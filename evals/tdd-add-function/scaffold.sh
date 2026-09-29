#!/usr/bin/env bash
set -euo pipefail
mkdir -p src test
cat > package.json <<'J'
{ "name": "fixture", "private": true, "type": "module", "scripts": { "test": "node --test" } }
J
cat > src/text.js <<'J'
export function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}
J
cat > test/text.test.js <<'J'
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { capitalize } from '../src/text.js';

test('capitalize uppercases the first letter', () => {
  assert.equal(capitalize('hello'), 'Hello');
});
J
git init -q && git config user.email eval@example.com && git config user.name eval && git add -A && git commit -qm "initial"
