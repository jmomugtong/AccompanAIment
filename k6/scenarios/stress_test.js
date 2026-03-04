/**
 * Stress Test: Gradual increase from 0 to 100+ concurrent users.
 *
 * Tests system capacity by slowly ramping up load beyond normal levels.
 * Identifies the breaking point and how the system degrades.
 *
 * Usage:
 *   k6 run k6/scenarios/stress_test.js
 *   k6 run --env BASE_URL=http://localhost:8000 k6/scenarios/stress_test.js
 */

import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Trend } from "k6/metrics";

const errorRate = new Rate("errors");
const uploadDuration = new Trend("upload_duration");
const queryDuration = new Trend("query_duration");

export const options = {
  stages: [
    { duration: "30s", target: 10 },
    { duration: "30s", target: 25 },
    { duration: "30s", target: 50 },
    { duration: "30s", target: 75 },
    { duration: "30s", target: 100 },
    { duration: "30s", target: 120 },
    { duration: "30s", target: 0 },
  ],
  thresholds: {
    http_req_duration: ["p(95)<5000"],
    http_req_failed: ["rate<0.01"],
    errors: ["rate<0.05"],
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
  }) || errorRate.add(1);

  queryDuration.add(healthRes.timings.duration);

  // Song melody query (simulated read-heavy workload)
  const queryRes = http.get(`${BASE_URL}/songs/1/melody`, {
    headers: { "Content-Type": "application/json" },
    tags: { name: "melody_query" },
  });
  check(queryRes, {
    "query status is not 5xx": (r) => r.status < 500,
  }) || errorRate.add(1);

  queryDuration.add(queryRes.timings.duration);

  // Simulate upload (POST with minimal payload)
  const uploadPayload = JSON.stringify({
    title: "Stress Test Song",
    style: "jazz",
  });
  const uploadRes = http.post(`${BASE_URL}/songs/upload`, uploadPayload, {
    headers: { "Content-Type": "application/json" },
    tags: { name: "upload" },
  });
  // Accept 4xx (validation/auth) -- only flag 5xx
  check(uploadRes, {
    "upload status is not 5xx": (r) => r.status < 500,
  }) || errorRate.add(1);

  uploadDuration.add(uploadRes.timings.duration);

  // Prometheus metrics endpoint
  const metricsRes = http.get(`${BASE_URL}/metrics`, {
    tags: { name: "metrics" },
  });
  check(metricsRes, {
    "metrics responds": (r) => r.status < 500,
  }) || errorRate.add(1);

  sleep(1);
}
