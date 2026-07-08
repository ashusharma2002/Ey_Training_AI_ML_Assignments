# Requirements — Express Rate Limiter

## 1. Project Overview

A custom sliding-window rate limiter middleware for Express.js, built without any third-party
rate-limiting library. It tracks request timestamps per client in memory and blocks clients
that exceed the configured threshold with an HTTP 429 response.

---

## 2. Functional Requirements

### 2.1 Rate Limiter Middleware (`rateLimiter.js`)

| # | Requirement |
|---|-------------|
| FR-01 | The middleware SHALL implement a **sliding window** algorithm (not fixed/leaky bucket). |
| FR-02 | The window size SHALL be configurable via `windowMs` (milliseconds). Default: `60,000` ms (1 minute). |
| FR-03 | The maximum allowed requests per window SHALL be configurable via `maxRequests`. Default: `60`. |
| FR-04 | The client key used to track requests SHALL default to `req.ip`. |
| FR-05 | A custom key function (`keyFn`) SHALL be supported to derive any string key from the request (e.g. user ID from a header). |
| FR-06 | When the limit is exceeded the middleware SHALL respond with **HTTP 429** and a JSON body containing `error`, `message`, and `retryAfter` fields. |
| FR-07 | A custom `message` string SHALL be configurable per limiter instance. |
| FR-08 | The middleware SHALL send a `Retry-After` header (seconds) on every 429 response. |
| FR-09 | The middleware SHALL send the following headers on every response (unless disabled): `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`. |
| FR-10 | Header sending SHALL be toggleable via a `headers` boolean option. Default: `true`. |
| FR-11 | Timestamps outside the current window SHALL be pruned on every request to keep memory usage bounded. |
| FR-12 | The factory function SHALL throw a `TypeError` if `windowMs` or `maxRequests` is not a positive number. |
| FR-13 | The module SHALL export a factory function that returns a configured Express `RequestHandler`. |

---

### 2.2 Server (`server.js`)

| # | Requirement |
|---|-------------|
| FR-14 | The server SHALL use Express.js and listen on `PORT` env variable, defaulting to `3000`. |
| FR-15 | A **global rate limiter** SHALL be applied to all routes: **10 requests per 30 seconds**, keyed by IP. |
| FR-16 | An **auth rate limiter** SHALL be applied to auth routes only: **5 requests per 60 seconds**, keyed by IP. |
| FR-17 | A **per-user rate limiter** SHALL be applied to user-data routes: **20 requests per 60 seconds**, keyed by `x-user-id` header (fallback to IP). |

---

### 2.3 API Endpoints

| Method | Route | Limiter(s) | Description |
|--------|-------|------------|-------------|
| GET | `/health` | Global | Returns `{ status: "ok" }` |
| POST | `/auth/login` | Global + Auth | Validates `username`/`password`; returns token or 401 |
| GET | `/api/data` | Global | Returns sample data array |
| GET | `/api/user-data` | Global + Per-user | Returns user-specific message |
| ANY | `*` (fallback) | Global | Returns 404 JSON error |

---

### 2.4 Auth Login Endpoint

| # | Requirement |
|---|-------------|
| FR-18 | The `POST /auth/login` endpoint SHALL accept a JSON body with `username` and `password` fields. |
| FR-19 | Valid credentials (`admin` / `secret`) SHALL return HTTP 200 with `{ message, token }`. |
| FR-20 | Invalid credentials SHALL return HTTP 401 with `{ error: "Invalid credentials" }`. |

---

## 3. Non-Functional Requirements

| # | Requirement |
|---|-------------|
| NFR-01 | The rate limiter store SHALL be **in-memory** (no Redis or external dependency). |
| NFR-02 | The middleware SHALL have **no runtime dependency** other than Express. |
| NFR-03 | The implementation SHALL use `'use strict'` mode. |
| NFR-04 | The server module SHALL be exportable (`module.exports = app`) to support automated testing. |
| NFR-05 | The server SHALL log the listening URL and active limiter configuration on startup. |
| NFR-06 | A global error handler SHALL catch unhandled errors and return HTTP 500 with a JSON response. |

---

## 4. Configuration Options Summary

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `windowMs` | `number` | `60000` | Sliding window duration in milliseconds |
| `maxRequests` | `number` | `60` | Max requests allowed within the window |
| `keyFn` | `function` | `(req) => req.ip` | Function to derive client identifier |
| `message` | `string` | `'Too many requests...'` | Message returned in 429 response body |
| `headers` | `boolean` | `true` | Whether to send `X-RateLimit-*` headers |

---

## 5. Dependencies

| Package | Version | Type | Purpose |
|---------|---------|------|---------|
| `express` | `^4.19.2` | production | HTTP server framework |
| `nodemon` | `^3.1.4` | dev | Auto-restart server on file changes |

---

## 6. Scripts

| Script | Command | Description |
|--------|---------|-------------|
| `npm start` | `node server.js` | Start the server |
| `npm run dev` | `nodemon server.js` | Start with auto-reload (development) |
