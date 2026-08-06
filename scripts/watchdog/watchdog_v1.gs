/**
 * watchdog_v1.gs — RidingHigh Pro external watchdog (Google Apps Script)
 * ─────────────────────────────────────────────────────────────────────────
 * WHY THIS EXISTS
 *   check_04, check_06 and detect_outage all run INSIDE GitHub Actions. On
 *   2026-08-06 GitHub Actions went into a Major Outage; 374 runs piled up in
 *   the queue, zero executed, and all three detectors stayed silent — because
 *   a guard that runs inside the system it guards is not a guard.
 *   This file runs on Google's infrastructure instead. Nothing it needs comes
 *   from GitHub.
 *
 * WHAT IT DOES
 *   Every 5 minutes, inside the market window, it asks the GitHub API two
 *   questions and mails an alert if either answer is bad:
 *     signal 1b  throughput — fewer than 10 runs COMPLETED in the last 15 min
 *                (gated: only counts if the hour before that was healthy)
 *     signal 2   queue depth — more than 25 runs sitting in `queued`
 *
 * NO CREDENTIALS. The repo is public, so the Actions API answers unauthenticated.
 * Do not add a token to this file — it lives in a Google account, not in a vault.
 */

// ═══ configuration — EDIT ALERT_TO BEFORE THE FIRST RUN ═══════════════════
var ALERT_TO       = 'PASTE_YOUR_EMAIL_HERE@example.com';  // ← EDIT ME
var REPO           = 'projects5069-creator/ridinghigh-pro';
var LOG_SHEET_NAME = 'watchdog_log';

// ═══ thresholds — every number below was MEASURED, not guessed ════════════
// Source: reports/2026-08-06_1439_watchdog_design.md (measured 2026-08-05 healthy
// baseline vs 2026-08-06 outage, 5-minute steps, both days).

// Activity window, UTC. The conservative INTERSECTION of the market session in
// both DST states (EDT 13:30-20:00Z, EST 14:30-21:00Z), so it needs no DST logic
// and no holiday calendar. Outside it the script exits silently.
var WINDOW_START_UTC_MIN = 14 * 60 + 45;   // 14:45Z
var WINDOW_END_UTC_MIN   = 19 * 60 + 45;   // 19:45Z

// Signal 1b — throughput. Healthy 2026-08-05: min 26, median 30, max 34 over 73
// samples. A threshold of 10 leaves a 2.6x margin. Fired 16:05Z on the outage day.
var RECENT_WINDOW_MIN      = 15;
var RECENT_MIN_COMPLETIONS = 10;

// Anti-false-alarm gate: "it was working and now it is not". On a weekend or a
// holiday nothing runs, so this stays false and the watchdog is silent WITHOUT
// knowing what a holiday is. Healthy days measure ~71 here with PER_PAGE=100.
var PRIOR_WINDOW_MIN      = 60;
var PRIOR_MIN_COMPLETIONS = 40;

// Signal 2 — queue depth. Healthy 2026-08-05: max 12. Outage day crossed 25 at
// 16:30Z and reached 302. Zero false fires on the healthy day.
var QUEUE_DEPTH_MAX = 25;

// MUST stay 100. With per_page=50 the prior-60-minute count reads ~21 even on a
// perfectly healthy day, the gate above never opens, and the watchdog never
// alerts at all. Verified against both days before this file was written.
var PER_PAGE = 100;

// Consecutive healthy readings required before an incident is declared over.
// Measured, not guessed: on 2026-08-06 the readings at 16:20Z and 16:25Z came
// back healthy for ten minutes in the MIDDLE of the outage (throughput briefly
// recovered to 10 and 13 while the queue was still climbing under the ceiling).
// With a streak of 1 that produced a false "recovered" mail and then a second
// alert five minutes later. A streak of 3 (= 15 minutes) rides straight over it
// and yields exactly one mail for the whole incident.
var HEALTHY_STREAK_TO_RESET = 3;

var PROP_ALERT_ACTIVE   = 'RH_WATCHDOG_ALERT_ACTIVE';
var PROP_HEALTHY_STREAK = 'RH_WATCHDOG_HEALTHY_STREAK';

// ═══ entry point — attach the 5-minute time-driven trigger to this ════════
function rhWatchdogRun() {
  var now = new Date();
  var queued = fetchQueuedCount_();               // null on any failure
  var completions = fetchCompletionTimes_();      // null on any failure
  var d = decide_(now.getTime(), queued, completions);

  logRow_(now, d);

  var props = PropertiesService.getScriptProperties();
  var alreadyAlerted = props.getProperty(PROP_ALERT_ACTIVE) === 'yes';

  if (d.alert) {
    props.setProperty(PROP_HEALTHY_STREAK, '0');
    if (!alreadyAlerted) {
      sendAlert_(now, d);
      props.setProperty(PROP_ALERT_ACTIVE, 'yes');
    }
  } else if (d.status === 'HEALTHY') {
    // Only a genuinely healthy reading advances the streak — never
    // FETCH_FAILED, PARTIAL or OUTSIDE_WINDOW. A flaky fetch or the overnight
    // gap must not be mistaken for recovery and clear the flag, or the same
    // ongoing incident would be mailed again the next morning.
    var streak = Number(props.getProperty(PROP_HEALTHY_STREAK) || 0) + 1;
    props.setProperty(PROP_HEALTHY_STREAK, String(streak));
    if (alreadyAlerted && streak >= HEALTHY_STREAK_TO_RESET) {
      props.deleteProperty(PROP_ALERT_ACTIVE);
      sendRecovery_(now, d);
    }
  }
}

// ═══ decision — PURE. No globals, no network, no clock. Testable as-is. ═══
function decide_(nowMs, queued, completions) {
  var d = new Date(nowMs);
  var utcMin = d.getUTCHours() * 60 + d.getUTCMinutes();
  var out = {
    utc: d.toISOString(), queued: queued,
    recent: null, prior: null,
    throughputBreach: false, queueBreach: false,
    alert: false, status: '', reason: ''
  };

  if (utcMin < WINDOW_START_UTC_MIN || utcMin > WINDOW_END_UTC_MIN) {
    out.status = 'OUTSIDE_WINDOW';
    return out;
  }
  if (queued === null && completions === null) {
    out.status = 'FETCH_FAILED';
    out.reason = 'both GitHub API calls failed';
    return out;
  }

  if (completions !== null) {
    out.recent = countBetween_(completions, nowMs - RECENT_WINDOW_MIN * 60000, nowMs);
    out.prior  = countBetween_(completions,
                               nowMs - (PRIOR_WINDOW_MIN + RECENT_WINDOW_MIN) * 60000,
                               nowMs - RECENT_WINDOW_MIN * 60000);
    out.throughputBreach = (out.recent < RECENT_MIN_COMPLETIONS &&
                            out.prior >= PRIOR_MIN_COMPLETIONS);
  }
  if (queued !== null) {
    out.queueBreach = queued > QUEUE_DEPTH_MAX;
  }

  out.alert = out.throughputBreach || out.queueBreach;
  if (out.alert) {
    out.status = 'ALERT';
    var why = [];
    if (out.throughputBreach) {
      why.push('throughput: ' + out.recent + ' completions in the last ' +
               RECENT_WINDOW_MIN + ' min (floor ' + RECENT_MIN_COMPLETIONS +
               '), after ' + out.prior + ' in the ' + PRIOR_WINDOW_MIN + ' min before');
    }
    if (out.queueBreach) {
      why.push('queue depth: ' + queued + ' runs queued (ceiling ' + QUEUE_DEPTH_MAX + ')');
    }
    out.reason = why.join(' | ');
  } else if (queued === null || completions === null) {
    out.status = 'PARTIAL';
    out.reason = 'one API call failed; judged on the other';
  } else {
    out.status = 'HEALTHY';
  }
  return out;
}

function countBetween_(times, fromMs, toMs) {
  var n = 0;
  for (var i = 0; i < times.length; i++) {
    if (times[i] >= fromMs && times[i] <= toMs) n++;
  }
  return n;
}

// ═══ network — every call swallowed; a failure logs but never mails ═══════
function fetchQueuedCount_() {
  try {
    var url = 'https://api.github.com/repos/' + REPO +
              '/actions/runs?status=queued&per_page=1';
    var res = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
    if (res.getResponseCode() !== 200) return null;
    var n = JSON.parse(res.getContentText()).total_count;
    return (typeof n === 'number') ? n : null;
  } catch (e) {
    return null;
  }
}

function fetchCompletionTimes_() {
  try {
    var url = 'https://api.github.com/repos/' + REPO +
              '/actions/runs?status=completed&per_page=' + PER_PAGE;
    var res = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
    if (res.getResponseCode() !== 200) return null;
    var runs = JSON.parse(res.getContentText()).workflow_runs;
    if (!runs) return null;
    var out = [];
    for (var i = 0; i < runs.length; i++) {
      // updated_at is the completion moment. It is an ISO-8601 Z string, so
      // Date.parse reads it as UTC regardless of the sheet's timezone.
      var ms = Date.parse(runs[i].updated_at);
      if (!isNaN(ms)) out.push(ms);
    }
    return out;
  } catch (e) {
    return null;
  }
}

// ═══ log — one row EVERY run, healthy included. This is the proof the ═════
// ═══ watchdog itself is alive. A log that stops IS the meta-signal.   ═════
function logRow_(now, d) {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sh = ss.getSheetByName(LOG_SHEET_NAME);
    if (!sh) {
      sh = ss.insertSheet(LOG_SHEET_NAME);
      sh.appendRow(['TimestampUTC', 'Status', 'Queued', 'Recent15',
                    'Prior60', 'Alert', 'Reason']);
    }
    sh.appendRow([now.toISOString(), d.status,
                  d.queued === null ? '' : d.queued,
                  d.recent === null ? '' : d.recent,
                  d.prior === null ? '' : d.prior,
                  d.alert ? 'YES' : '', d.reason]);
  } catch (e) {
    // A failure to log must never break the alert path.
  }
}

// ═══ mail ═════════════════════════════════════════════════════════════════
function sendAlert_(now, d) {
  MailApp.sendEmail(ALERT_TO,
    'RH WATCHDOG: GitHub Actions pipeline is not producing',
    'Detected at ' + now.toISOString() + '\n\n' +
    d.reason + '\n\n' +
    '--- both signals at this moment ---\n' +
    'queued runs        : ' + (d.queued === null ? 'unavailable' : d.queued) +
      '   (ceiling ' + QUEUE_DEPTH_MAX + ')\n' +
    'completions 15 min : ' + (d.recent === null ? 'unavailable' : d.recent) +
      '   (floor ' + RECENT_MIN_COMPLETIONS + ')\n' +
    'completions 60 min : ' + (d.prior === null ? 'unavailable' : d.prior) +
      '   (gate ' + PRIOR_MIN_COMPLETIONS + ')\n\n' +
    'First check https://www.githubstatus.com — on 2026-08-06 this exact\n' +
    'pattern was a GitHub-side Actions outage, not a repo problem.\n\n' +
    'https://github.com/' + REPO + '/actions\n\n' +
    'One mail per incident. The next one arrives only after a healthy reading.');
}

function sendRecovery_(now, d) {
  MailApp.sendEmail(ALERT_TO,
    'RH WATCHDOG: recovered',
    'Healthy again at ' + now.toISOString() + '\n\n' +
    'queued ' + d.queued + ', ' + d.recent + ' completions in the last ' +
    RECENT_WINDOW_MIN + ' min.\n' +
    'Alerting is re-armed for the next incident.');
}

// ═══ manual test — run this from the editor to prove the mail path works ══
// It bypasses the thresholds entirely and sends one alert with fake numbers.
// It does NOT touch the dedup flag, so it cannot mask a real incident.
function rhWatchdogTestAlert() {
  sendAlert_(new Date(), {
    queued: 999, recent: 0, prior: 120, alert: true, status: 'ALERT',
    reason: 'MANUAL TEST — triggered by hand from the Apps Script editor'
  });
}
