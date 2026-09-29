#!/usr/bin/env bash
set -euo pipefail
mkdir -p src test
cat > package.json <<'J'
{ "name": "fixture", "private": true, "type": "module", "scripts": { "test": "node --test" } }
J
cat > test/wc.test.js <<'J'
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { countWords } from '../src/wc.js';

test('counts whitespace-separated words', () => {
  assert.equal(countWords('hello world'), 2);
  assert.equal(countWords('  a  b\nc '), 3);
});

test('empty text has no words', () => {
  assert.equal(countWords(''), 0);
  assert.equal(countWords('   '), 0);
});
J
git init -q && git config user.email eval@example.com && git config user.name eval && git add -A && git commit -qm "initial"
