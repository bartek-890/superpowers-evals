#!/usr/bin/env bash
set -euo pipefail
mkdir -p src test
cat > package.json <<'J'
{ "name": "fixture", "private": true, "type": "module", "scripts": { "test": "node --test" } }
J
cat > src/users.js <<'J'
export function displayName(user) {
  if (!user || !user.name) return 'Anonymous';
  return user.name.trim();
}
J
cat > src/comments.js <<'J'
import { displayName } from './users.js';

// author is null when the commenting account was deleted.
export function renderComment(comment) {
  return `${displayName(comment.author)}: ${comment.body}`;
}
J
cat > test/comments.test.js <<'J'
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { renderComment } from '../src/comments.js';

test('renders author name', () => {
  assert.equal(renderComment({ author: { name: 'Ada ' }, body: 'hi' }), 'Ada: hi');
});

test('deleted author renders as Anonymous', () => {
  assert.equal(renderComment({ author: null, body: 'hi' }), 'Anonymous: hi');
});
J
cat > REVIEW.md <<'J'
Review notes on src/users.js:

1. The null check in displayName is dead code - every user has a name. Remove it so the function is a one-liner.
2. Please add a short JSDoc comment on displayName describing what it returns.
J
git init -q && git config user.email eval@example.com && git config user.name eval && git add -A && git commit -qm "initial"
