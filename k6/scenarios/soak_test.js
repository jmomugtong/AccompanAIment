/**
 * Soak Test: Sustained load of 50 concurrent users for 10 minutes.
 *
 * Tests system stability over an extended period at moderate load.
 * Detects memory leaks, connection pool exhaustion, and gradual degradation.
 *
 * Usage:
 *   k6 run k6/scenarios/soak_test.js
 *   k6 run --env BASE_URL=http://localhost:8000 k6/scenarios/soak_test.js
 */

import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Trend } from "k6/metrics";

const errorRate = new Rate("errors");
const uploadDuration = new Trend("upload_duration");
const queryDuration = new Trend("query_duration");

export const options = {
  stages: [
    { duration: "30s", target: 50 },
    { duration: "10m", target: 50 },
    { duration: "30s", target: 0 },
  ],
  thresholds: {
    http_req_duration: ["p(95)<5000", "p(99)<8000"],
    http_req_failed: ["rate<0.01"],
    errors: ["rate<0.02"],
    upload_duration: ["p(95)<5000"],
    query_duration: ["p(95)<2000"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

export default function () {
  // Health check
  const healthRes = http.get(`${BASE_URL}/health`, {
    tags: { name: "health" },
  });
  check(healthRes, {
    "health status is 200": (r) => r.status === 200,
    "health body is valid": (r) => {
      try {
        return JSON.parse(r.body).status === "healthy";
      } catch (e) {
        return false;
      }
    },
  }) || errorRate.add(1);

  queryDuration.add(healthRes.timings.duration);

  // Melody query -- read-heavy workload
  const songId = Math.floor(Math.random() * 10) + 1;
  const queryRes = http.get(`${BASE_URL}/songs/${songId}/melody`, {
    headers: { "Content-Type": "application/json" },
    tags: { name: "melody_query" },
  });
  check(queryRes, {
    "query does not error": (r) => r.status < 500,
  }) || errorRate.add(1);

  queryDuration.add(queryRes.timings.duration);

  // Simulate generation request
  const genPayload = JSON.stringify({
    chords: "Cmaj7 | Dm7 | G7 | Cmaj7",
    style: "jazz",
    tempo: 120,
    time_signature: "4/4",
  });
  const genRes = http.post(
    `${BASE_URL}/songs/${songId}/generate-piano`,
    genPayload,
    {
      headers: { "Content-Type": "application/json" },
      tags: { name: "generate" },
    }
  );
  check(genRes, {
    "generate does not error": (r) => r.status < 500,
  }) || errorRate.add(1);

  uploadDuration.add(genRes.timings.duration);

  // Metrics endpoint (observability check)
  const metricsRes = http.get(`${BASE_URL}/metrics`, {
    tags: { name: "metrics" },
  });
  check(metricsRes, {
    "metrics responds": (r) => r.status < 500,
  }) || errorRate.add(1);

  sleep(1);
}
