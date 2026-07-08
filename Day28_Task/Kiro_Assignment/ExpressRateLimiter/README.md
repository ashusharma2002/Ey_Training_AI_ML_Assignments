# Express Rate Limiter Middleware

A sliding window rate limiter for Express that restricts users to a maximum number of requests within a rolling time window. Returns HTTP 429 when the limit is exceeded.

## Features

- **Sliding window algorithm** — tracks requests per client within a rolling time window
- **Configurable limits** — adjust max requests and window size per route
- **Client identification** — defaults to IP address, customizable via `keyFn`
- **Standard headers** — sends `X-RateLimit-*` and `Retry-After` headers
- **In-memory storage** — automatic cleanup of expired timestamps

## Installation

```bash
npm install
```

## Quick Start

```bash
npm start
```

Server runs on `http://localhost:3000` with:
- Global limit: 10 requests / 30 seconds
- Auth limit: 5 requests / 60 seconds

## Usage

### Basic Example

```javascript
const express     = require('express');
const rateLimiter = require('./rateLimiter');

const app = express();

// 100 requests per 15 minutes
app.use(rateLimiter({
  windowMs:    15 * 60 * 1000,
  maxRequests: 100,
}));

app.get('/api/data', (req, res) => {
  res.json({ message: 'Success' });
});

app.listen(3000);
```

### Route-Specific Limiter

```javascript
const authLimiter = rateLimiter({
  windowMs:    60 * 1000, // 1 minute
  maxRequests: 5,
  message:     'Too many auth attempts.',
});

app.post('/auth/login', authLimiter, (req, res) => {
  // handle login
});
```

### Custom Key Function

```javascript
// Rate limit per user ID instead of IP
app.use(rateLimiter({
  windowMs:    60 * 1000,
  maxRequests: 20,
  keyFn:       (req) => req.headers['x-user-id'] || req.ip,
}));
```

## Configuration Options

| Option       | Type     | Default                                    | Description                                        |
|--------------|----------|--------------------------------------------|----------------------------------------------------|
| `windowMs`   | number   | `60000` (1 minute)                         | Time window in milliseconds                        |
| `maxRequests`| number   | `60`                                       | Maximum requests allowed per window                |
| `keyFn`      | function | `(req) => req.ip`                          | Function to derive client identifier from request  |
| `message`    | string   | `'Too many requests, please try again later.'` | Error message in 429 response                      |
| `headers`    | boolean  | `true`                                     | Send `X-RateLimit-*` headers on every response     |

## Response Headers

When a request is processed, the middleware adds:

- `X-RateLimit-Limit` — maximum requests allowed
- `X-RateLimit-Remaining` — requests remaining in current window
- `X-RateLimit-Reset` — Unix timestamp when the window resets

When limit is exceeded, also includes:

- `Retry-After` — seconds until a request slot becomes available

## HTTP 429 Response

```json
{
  "error": "Too Many Requests",
  "message": "Too many requests, please try again later.",
  "retryAfter": 12
}
```

## Testing

Try hitting an endpoint repeatedly to trigger the rate limit:

```bash
# Global limit test (10 requests / 30 seconds)
for i in {1..15}; do curl http://localhost:3000/health; done

# Auth limit test (5 requests / 60 seconds)
for i in {1..10}; do curl -X POST http://localhost:3000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"secret"}'; done
```

## Notes

- **In-memory only** — not suitable for multi-server deployments without a shared store (e.g., Redis)
- **Sliding window** — more accurate than fixed window, prevents burst at window boundaries
- **Automatic cleanup** — expired timestamps are pruned on each request, keeping memory bounded

## License

MIT
