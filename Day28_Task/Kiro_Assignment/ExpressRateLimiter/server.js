'use strict';

const express     = require('express');
const rateLimiter = require('./rateLimiter');

const app  = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

// ---------------------------------------------------------------------------
// Global rate limit: 10 requests per 30 seconds for all routes
// ---------------------------------------------------------------------------
app.use(
  rateLimiter({
    windowMs:    30 * 1000, // 30 seconds
    maxRequests: 10,
    message:     'Global limit exceeded. Please slow down.',
  })
);

// ---------------------------------------------------------------------------
// Stricter limit on the auth routes: 5 requests per 60 seconds
// ---------------------------------------------------------------------------
const authLimiter = rateLimiter({
  windowMs:    60 * 1000, // 1 minute
  maxRequests: 5,
  message:     'Too many auth attempts. Try again in a minute.',
});

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

/** Public health check — still subject to the global limiter above. */
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

/** Simulated login — protected by both the global limiter and authLimiter. */
app.post('/auth/login', authLimiter, (req, res) => {
  const { username, password } = req.body;

  // Dummy credential check — replace with real auth logic.
  if (username === 'admin' && password === 'secret') {
    return res.json({ message: 'Login successful', token: 'dummy-jwt-token' });
  }
  res.status(401).json({ error: 'Invalid credentials' });
});

/** Example protected resource. */
app.get('/api/data', (req, res) => {
  res.json({
    message: 'Here is your data',
    items:   [1, 2, 3, 4, 5],
  });
});

/**
 * Route-specific limiter example — per-user key instead of IP.
 * Useful when a proxy sits in front and all requests share the same IP.
 */
const perUserLimiter = rateLimiter({
  windowMs:    60 * 1000, // 1 minute
  maxRequests: 20,
  // Derive the key from a custom header (e.g. a user-id set by an auth layer).
  keyFn:       (req) => req.headers['x-user-id'] || req.ip,
  message:     'Per-user limit exceeded.',
});

app.get('/api/user-data', perUserLimiter, (req, res) => {
  res.json({ message: 'User-specific data endpoint' });
});

// ---------------------------------------------------------------------------
// 404 fallback
// ---------------------------------------------------------------------------
app.use((req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

// ---------------------------------------------------------------------------
// Global error handler
// ---------------------------------------------------------------------------
app.use((err, req, res, _next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Internal server error' });
});

// ---------------------------------------------------------------------------
// Start
// ---------------------------------------------------------------------------
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
  console.log('Rate limiter active: 10 req / 30 s (global), 5 req / 60 s (auth)');
});

module.exports = app; // exported for testing
