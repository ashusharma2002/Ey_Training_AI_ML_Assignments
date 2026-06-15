# PayStream Real-Time Payment Platform
## Queue vs Event Bus Classification

---

# Overview

PayStream is a B2B payment processor handling millions of transactions per day.

The messaging layer must ensure:

- Reliable payment processing
- Exactly-once settlement
- Real-time fraud checks
- Customer notifications
- Analytics processing
- Future scalability

The architecture consists of:

```text
Merchant API
      │
      ▼
Payment Core
      │
 ┌────┼────┬───────┐
 ▼    ▼    ▼       ▼
Ledger Fraud Notification Analytics
Service Engine Hub       Pipeline
```

---

# Decision Rules

## Use Queue When

- Exactly one consumer should process a message
- Task/command execution is required
- Retry handling is important
- Work must not be duplicated
- Load balancing across workers is needed

### Queue Flow

```text
Producer
   │
   ▼
 Queue
   │
   ▼
Single Consumer

Message processed once
```

---

## Use Event Bus When

- Multiple services need the same information
- Publish/Subscribe pattern is required
- Fan-out is needed
- New subscribers may be added later
- Broadcasting events is the goal

### Event Bus Flow

```text
Publisher
    │
    ▼
 Event Bus
 ┌──┼───┬───┐
 ▼  ▼   ▼   ▼
A   B   C   D

Same event delivered to many consumers
```

---

# Scenario A - Settlement Command

## Requirement

When a payment is approved, Payment Core sends a

"Debit Merchant Account"

instruction to Ledger Service.

Requirements:

- Exactly once delivery
- Single processor
- Durable retries
- No duplicates

## Classification

### Queue 

## Why?

This is a command that must be executed exactly once by Ledger Service.

Only one consumer should process it.

If Ledger Service is unavailable, the message must wait and retry.

## Flow

```text
Payment Core
      │
      ▼
 Settlement Queue
      │
      ▼
 Ledger Service

Exactly once processing
```

---

# Scenario B - Payment Received Broadcast

## Requirement

After settlement:

- Notification Hub sends SMS
- Analytics records revenue
- Fraud Engine updates spending profile

All services react independently.

## Classification

### Event Bus 

## Why?

One event triggers multiple consumers.

All services need the same event simultaneously.

This is a classic Publish/Subscribe pattern.

## Flow

```text
Ledger Service
      │
      ▼
 Payment Received Event
      │
      ▼
  Event Bus
 ┌────┼───────┬─────────┐
 ▼    ▼       ▼
SMS Analytics Fraud

Multiple independent consumers
```

---

# Scenario C - SMS / Push Notifications

## Requirement

Notification Hub sends thousands of alerts.

Each alert:

- Must be processed once
- Should not be duplicated
- Must be distributed across worker pool

## Classification

### Queue 

## Why?

Each SMS should be handled by exactly one worker.

Multiple workers compete for jobs.

This is a work distribution pattern.

## Flow

```text
Notification Hub
       │
       ▼
 Notification Queue
       │
 ┌─────┼─────┐
 ▼     ▼     ▼
W1    W2    W3

One worker handles one message
```

---

# Scenario D - Fraud Score Request

## Requirement

Before authorization:

Payment Core requests fraud score.

Characteristics:

- Request/Reply
- Single fraud engine
- Wait for response
- 200ms timeout

## Classification

### Queue 

## Why?

This is a dedicated processing task.

Only Fraud Engine should process the request.

No broadcasting is needed.

## Flow

```text
Payment Core
      │
      ▼
 Fraud Request Queue
      │
      ▼
 Fraud Engine
      │
      ▼
 Fraud Score Response
```

---

# Scenario E - Account State Change Events

## Requirement

Account state changes such as:

- Account Activated
- Account Suspended
- Account Closed

Many systems may need these events.

Future consumers may be added.

## Classification

### Event Bus 

## Why?

Multiple services can independently subscribe.

Producer should not know consumers.

New subscribers can be added without changing producer code.

## Flow

```text
Account Service
      │
      ▼
Account Changed Event
      │
      ▼
 Event Bus
 ┌────┼────┬─────┐
 ▼    ▼    ▼
CRM Audit Analytics

Future consumers can subscribe
```

---

# Scenario F - End-of-Day Reconciliation

## Requirement

Daily reconciliation jobs:

- Must run once
- Need retry handling
- Require guaranteed execution
- Distributed among workers

## Classification

### Queue 

## Why?

This is a background processing task.

Only one worker should process a reconciliation job.

Reliability and retries are required.

## Flow

```text
Scheduler
    │
    ▼
Reconciliation Queue
    │
    ▼
Worker

Guaranteed execution
```

---

# Final Answer Sheet

| ID | Integration | Classification | Key Deciding Factor |
|----|-------------|---------------|---------------------|
| A | Settlement Command | Queue | Exactly-once processing by a single consumer |
| B | Payment Received Broadcast | Event Bus | Multiple independent consumers need same event |
| C | SMS / Push Notifications | Queue | Competing consumers and load balancing |
| D | Fraud Score Request | Queue | Request/Reply with dedicated processor |
| E | Account State Change Events | Event Bus | Publish/Subscribe and future extensibility |
| F | End-of-Day Reconciliation | Queue | Guaranteed execution with retries |

---

# Architecture Summary

```text
                    ┌───────────────────┐
                    │   Merchant API    │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │   Payment Core    │
                    └───┬─────┬─────┬───┘
                        │     │     │
                        │     │     │
                        ▼     ▼     ▼

                  [QUEUE] [QUEUE] [EVENT BUS]
                   A,D,F     C        B,E

                        │     │     │

                   Ledger  Notification
                   Fraud     Workers
                             Analytics
                             Subscribers
```

# Conclusion

### Queue Scenarios
- A - Settlement Command
- C - SMS / Push Notifications
- D - Fraud Score Request
- F - End-of-Day Reconciliation

### Event Bus Scenarios
- B - Payment Received Broadcast
- E - Account State Change Events



- **Queue = One message → One consumer**
- **Event Bus = One event → Many consumers**