import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import path from 'node:path';
const DRAFT_CSV_PATH = path.resolve(process.cwd(), 'docs', 'draft_result.csv');
const RAW_DRAFT = readFileSync(DRAFT_CSV_PATH, 'utf8');

function parseCsv(text) {
  const rows = [];
  let currentField = '';
  let currentRow = [];
  let inQuotes = false;

  const pushField = () => {
    currentRow.push(currentField);
    currentField = '';
  };

  const pushRow = () => {
    pushField();
    rows.push(currentRow);
    currentRow = [];
  };

  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    if (char === '"') {
      if (inQuotes && text[i + 1] === '"') {
        currentField += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (char === ',' && !inQuotes) {
      pushField();
      continue;
    }

    if ((char === '\n' || char === '\r') && !inQuotes) {
      if (char === '\r' && text[i + 1] === '\n') {
        i++;
      }
      pushRow();
      continue;
    }

    currentField += char;
  }

  if (currentField.length > 0 || currentRow.length > 0) {
    pushField();
    rows.push(currentRow);
  }
  return rows.filter(row => row.some(value => value.trim().length > 0));
}

const [headerRow, ...rows] = parseCsv(RAW_DRAFT);
const headers = headerRow.map(h => h.trim());
const draftRows = rows.map(row => {
  const obj = {};
  headers.forEach((header, index) => {
    obj[header] = (row[index] ?? '').trim();
  });
  return obj;
}).filter(row => (row.Player || '').length > 0);
const TEAM_SIZE = 15;

function getFantasyTeam(row) {
  const value = row['Fantasy Team'] ?? row['Fantasy Team '] ?? '';
  return value.trim();
}

function summarizeTeams() {
  const counts = new Map();
  draftRows.forEach(row => {
    const team = getFantasyTeam(row);
    if (!team) return;
    counts.set(team, (counts.get(team) || 0) + 1);
  });
  return counts;
}

const teamCounts = summarizeTeams();
const teamCount = teamCounts.size;

test('each fantasy team drafted exactly 15 players', () => {
  assert.ok(teamCount > 0, 'No fantasy teams were parsed from draft results.');
  for (const [team, count] of teamCounts.entries()) {
    assert.equal(
      count,
      TEAM_SIZE,
      `Team "${team}" drafted ${count} players instead of ${TEAM_SIZE}.`
    );
  }
});

test('drafted players are unique across the league', () => {
  const seenPlayers = new Set();
  draftRows.forEach(row => {
    const playerName = (row.Player || '').trim();
    assert.ok(playerName, 'Encountered a draft pick without a player name.');
    const key = playerName.toLowerCase();
    assert.ok(
      !seenPlayers.has(key),
      `Player "${playerName}" appears multiple times in draft_result.csv.`
    );
    seenPlayers.add(key);
  });
});

test('every draft round captured picks for all teams', () => {
  const picksByRound = new Map();
  draftRows.forEach(row => {
    const round = Number(row.Round);
    const team = getFantasyTeam(row);
    if (!team || Number.isNaN(round)) return;
    if (!picksByRound.has(round)) {
      picksByRound.set(round, new Set());
    }
    picksByRound.get(round).add(team);
  });

  assert.ok(picksByRound.size >= TEAM_SIZE, 'Expected at least 15 draft rounds.');
  for (const [round, teams] of picksByRound.entries()) {
    assert.equal(
      teams.size,
      teamCount,
      `Round ${round} only recorded picks for ${teams.size}/${teamCount} teams.`
    );
  }
});
