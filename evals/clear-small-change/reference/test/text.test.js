import { test } from 'node:test';
import assert from 'node:assert/strict';
import { capitalizeFirst } from '../src/text.js';

test('capitalize uppercases the first letter', () => {
  assert.equal(capitalizeFirst('hello'), 'Hello');
});
