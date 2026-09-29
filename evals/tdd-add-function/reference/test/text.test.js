import { test } from 'node:test';
import assert from 'node:assert/strict';
import { capitalize, truncate } from '../src/text.js';

test('capitalize uppercases the first letter', () => {
  assert.equal(capitalize('hello'), 'Hello');
});

test('truncate cuts to exactly max characters ending in ...', () => {
  assert.equal(truncate('hello world', 8), 'hello...');
});

test('truncate leaves short strings alone', () => {
  assert.equal(truncate('hello', 5), 'hello');
});
