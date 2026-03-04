/**
 * Spike Test: Sudden traffic spike from 0 to 100 concurrent users.
 *
 * Tests system behavior under a sudden, sharp increase in load.
 * Useful for verifying auto-scaling and graceful degradation.
 *
 * Usage:
 *   k6 run k6/scenarios/spike_test.js
 *   k6 run --env BASE_URL=http://localhost:8000 k6/scenarios/spike_test.js
 */

import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Trend } from "k6/metrics";

const errorRate = new Rate("errors");
const uploadDuration = new Trend("upload_duration");
const queryDuration = new Trend("query_duration");

export const options = {
  stages: [
    { duration: "5s", target: 0 },
    { duration: "5s", target: 100 },
    { duration: "30s", target: 100 },
    { duration: "10s", target: 0 },
  ],
  thresholds: {
    http_req_duration: ["p(95)<5000"],
    http_req_failed: ["rate<0.01"],
    errors: ["rate<0.05"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

export default function () {
  // Health check endpoint
  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    "health status is 200": (r) => r.status === 200,
    "health response is healthy": (r) => {
      try {
        return JSON.parse(r.body).status === "healthy";
      } catch (e) {
        return false;
      }
    },
  }) || errorRate.add(1);

  queryDuration.add(healthRes.timings.duration);

  // Simulate song query endpoint
  const queryRes = http.get(`${BASE_URL}/songs/1/melody`, {
    headers: { "Content-Type": "application/json" },
    tags: { name: "melody_query" },
  });
  // 404 is acceptable for a non-existent song; we only flag server errors
  check(queryRes, {
    "query status is not 5xx": (r) => r.status < 500,
  }) || errorRate.add(1);

  queryDuration.add(queryRes.timings.duration);

  // Simulate metrics endpoint
  const metricsRes = http.get(`${BASE_URL}/metrics`, {
    tags: { name: "metrics" },
  });
  check(metricsRes, {
    "metrics endpoint responds": (r) => r.status < 500,
  }) || errorRate.add(1);

  sleep(0.5);
}
