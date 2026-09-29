#!/usr/bin/env bash
set -euo pipefail
mkdir -p src test
cat > package.json <<'J'
{ "name": "fixture", "private": true, "type": "module", "scripts": { "test": "node --test" } }
J
cat > src/dates.js <<'J'
// Parse an ISO calendar date (YYYY-MM-DD) into a UTC Date.
export function parseDate(s) {
  const [y, m, d] = s.split('-').map(Number);
  return new Date(Date.UTC(y, m, d));
}

export function formatDate(date) {
  return date.toISOString().slice(0, 10);
}

export function addDays(date, days) {
  return new Date(date.getTime() + days * 86400000);
}
J
cat > src/invoice.js <<'J'
import { parseDate, formatDate, addDays } from './dates.js';

// Due date = issue date + payment terms.
export function dueDate(issued, termsDays) {
  return formatDate(addDays(parseDate(issued), termsDays));
}
J
cat > src/report.js <<'J'
import { parseDate } from './dates.js';

// Month label for the monthly revenue report, e.g. "2026-03".
export function reportMonth(isoDate) {
  const d = parseDate(isoDate);
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}`;
}
J
cat > test/invoice.test.js <<'J'
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { dueDate } from '../src/invoice.js';

test('net-14 invoice issued Jan 30 is due Feb 13', () => {
  assert.equal(dueDate('2026-01-30', 14), '2026-02-13');
});
J
git init -q && git add -A && git -c user.email=eval@example.com -c user.name=eval commit -qm "initial"
