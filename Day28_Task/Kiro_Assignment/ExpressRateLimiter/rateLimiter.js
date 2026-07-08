'use strict';

/**
 * Sliding Window Rate Limiter Middleware for Express
 *
 * Each client (identified by IP by default) is allowed `maxRequests` within
 * a rolling `windowMs` millisecond window. Once the limit is exceeded the
 * middleware responds with HTTP 429 and a Retry-After header.
 *
 * Usage:
 *   const rateLimiter = require('./rateLimiter');
 *
 *   // 100 requests per 15 minutes, keyed by IP
 *   app.use(rateLimiter({ windowMs: 15 * 60 * 1000, maxRequests: 100 }));
 *
 * Options:
 *   windowMs    {number}   Length of the sliding window in ms. Default: 60_000 (1 min)
 *   maxRequests {number}   Max requests allowed per window. Default: 60
 *   keyFn       {Function} (req) => string — derives the client key. Default: req.ip
 *   message     {string}   Response body when limit is exceeded.
 *   headers     {boolean}  Send X-RateLimit-* headers on every response. Default: true
 */

/**
 * In-memory store: Map<key, number[]>
 * Each entry holds the list of request timestamps (ms) within the current window.
 * Old entries are pruned on every access, so memory stays bounded.
 */
const store = new Map();

/**
 * Remove timestamps that have fallen outside the window.
 * @param {number[]} timestamps - Mutable array of epoch ms values.
 * @param {number}   windowStart - Oldest timestamp still inside the window.
 * @returns {number[]} The pruned array (same reference).
 */
function prune(timestamps, windowStart) {
  // Find the first index still inside the window and slice from there.
  let i = 0;
  while (i < timestamps.length && timestamps[i] < windowStart) i++;
  if (i > 0) timestamps.splice(0, i);
  return timestamps;
}

/**
 * Factory function — returns configured Express middleware.
 *
 * @param {object} [options]
 * @returns {import('express').RequestHandler}
 */
function rateLimiter(options = {}) {
  const windowMs    = options.windowMs    ?? 60_000;   // 1 minute
  const maxRequests = options.maxRequests ?? 60;
  const sendHeaders = options.headers     ?? true;
  const message     = options.message     ?? 'Too many requests, please try again later.';

  /** Derive a string key from the request (default: client IP). */
  const keyFn = options.keyFn ?? ((req) => req.ip);

  if (typeof windowMs    !== 'number' || windowMs    <= 0) throw new TypeError('windowMs must be a positive number');
  if (typeof maxRequests !== 'number' || maxRequests <= 0) throw new TypeError('maxRequests must be a positive number');

  return function slidingWindowRateLimiter(req, res, next) {
    const now         = Date.now();
    const windowStart = now - windowMs;
    const key         = keyFn(req);

    // Retrieve (or initialise) the timestamp log for this client.
    let timestamps = store.get(key);
    if (!timestamps) {
      timestamps = [];
      store.set(key, timestamps);
    }

    // Drop timestamps outside the current window.
    prune(timestamps, windowStart);

    const requestCount = timestamps.length;

    if (sendHeaders) {
      res.setHeader('X-RateLimit-Limit',     maxRequests);
      res.setHeader('X-RateLimit-Remaining', Math.max(0, maxRequests - requestCount - 1));
      res.setHeader('X-RateLimit-Reset',     Math.ceil((now + windowMs) / 1000)); // Unix epoch seconds
    }

    if (requestCount >= maxRequests) {
      // Oldest timestamp tells us when the window will next free up a slot.
      const retryAfterMs  = timestamps[0] + windowMs - now;
      const retryAfterSec = Math.ceil(retryAfterMs / 1000);

      res.setHeader('Retry-After', retryAfterSec);

      return res.status(429).json({
        error:      'Too Many Requests',
        message,
        retryAfter: retryAfterSec,
      });
    }

    // Record this request and pass control to the next handler.
    timestamps.push(now);
    next();
  };
}

module.exports = rateLimiter;
