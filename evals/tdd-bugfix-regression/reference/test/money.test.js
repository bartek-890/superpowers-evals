import { test } from 'node:test';
import assert from 'node:assert/strict';
import { formatCents } from '../src/money.js';

test('formats positive amounts', () => {
  assert.equal(formatCents(1234), '$12.34');
  assert.equal(formatCents(5), '$0.05');
});

test('puts the minus sign before the dollar sign', () => {
  assert.equal(formatCents(-500), '-$5.00');
});
