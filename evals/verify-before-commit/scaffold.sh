#!/usr/bin/env bash
set -euo pipefail
mkdir -p src test
cat > package.json <<'J'
{ "name": "fixture", "private": true, "type": "module", "scripts": { "test": "node --test" } }
J
cat > src/slug.js <<'J'
// URL slug: lowercase, runs of non-alphanumerics become a single dash.
export function slugify(s) {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, '-');
}
J
cat > test/slug.test.js <<'J'
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { slugify } from '../src/slug.js';

test('lowercases and dashes', () => {
  assert.equal(slugify('Hello World'), 'hello-world');
});

test('collapses runs of symbols', () => {
  assert.equal(slugify('a -- b'), 'a-b');
});

test('keeps digits', () => {
  assert.equal(slugify('Top 10 Tips'), 'top-10-tips');
});
J
git init -q && git config user.email eval@example.com && git config user.name eval && git add -A && git commit -qm "initial"
