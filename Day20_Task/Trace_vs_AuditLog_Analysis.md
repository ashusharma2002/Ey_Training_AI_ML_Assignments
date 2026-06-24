# Day 20 – Observability and Governance
## Trace / Spans vs Audit Logs – End-to-End Analysis

---

# Table of Contents

1. Introduction
2. Trace / Spans
3. Audit Logs
4. Architecture Overview
5. Ticket 02 Analysis
6. Ticket 03 Analysis
7. Ticket 04 Analysis
8. Ticket 05 Analysis
9. Ticket 06 Analysis
10. Ticket 08 Analysis
11. Comparison Table
12. Conclusion

---

# Introduction

Modern AI and distributed systems require two important mechanisms:

1. **Trace / Spans** (Observability)
2. **Audit Logs** (Governance)

Although both record system activities, they serve different purposes.

- Trace/Spans help engineers understand request execution, latency, and failures.
- Audit Logs help compliance, security, and regulators verify decisions and ensure records cannot be altered.

Understanding when to use each mechanism is essential for building secure, observable, and compliant AI systems.

---

# Trace / Spans

## Definition

Trace/Spans capture the journey of a request through different services and components.

A trace consists of multiple spans, where each span represents one operation performed during request processing.

---

## Purpose

Trace/Spans are mainly used for:

- Request tracking
- Debugging
- Root cause analysis
- Performance monitoring
- Latency analysis
- Dependency visualization

---

## Example

```text
User Request
     |
     v
API Gateway
     |
     v
Authentication Service
     |
     v
LLM Service
     |
     v
Database
```

Trace records:

- Which services were called
- Execution order
- Response times
- Failure locations

---

## Characteristics

| Feature | Trace/Spans |
|----------|-------------|
| Request Flow | Yes |
| Error Analysis | Yes |
| Performance Monitoring | Yes |
| Latency Tracking | Yes |
| Compliance Evidence | No |
| Tamper Protection | No |
| Long-Term Retention | Usually No |

---

# Audit Logs

## Definition

Audit Logs are immutable records of important system actions and decisions.

They provide accountability and compliance evidence.

---

## Purpose

Audit Logs are used for:

- Regulatory compliance
- Security investigations
- Decision tracking
- User accountability
- Governance
- Tamper detection

---

## Example

```text
Loan Approved
User: Manager123
Model Version: v5.2
Timestamp: 2026-06-24
Decision: Approved
```

---

## Characteristics

| Feature | Audit Log |
|----------|------------|
| Compliance Evidence | Yes |
| Decision Tracking | Yes |
| Accountability | Yes |
| Tamper Detection | Yes |
| Debugging | No |
| Performance Analysis | No |
| Call Tree Visualization | No |

---

# Architecture Overview

```text
                    USER REQUEST
                           |
                           v

                  +----------------+
                  | Trace / Spans  |
                  +----------------+
                           |
                           v

          API -> Service A -> Service B -> LLM

                           |
                           v

                Error / Latency Analysis


------------------------------------------------


                  +----------------+
                  |   Audit Log    |
                  +----------------+
                           |
                           v

                  Decision Approved
                  Model Version Used
                  Guardrail Executed
                  User Identity
                  Timestamp
                  Hash Verification
```

---

# Ticket 02 Analysis

## Problem Statement

A regulator demands:

> Who approved loan #88213, on what model version, with what inputs — and proof it was never altered.

---

## Correct Answer

### Audit Log ✅

---

## Why This Answer?

The request asks:

- Who approved the loan
- Which model version was used
- What inputs were used
- Proof that records have not been modified

These requirements are related to governance, compliance, accountability, and data integrity.

Audit Logs maintain immutable records suitable for regulatory audits.

---

## Why Not Trace / Spans?

Trace/Spans focus on:

- Request execution
- Service flow
- Performance monitoring

They do not provide long-term tamper-proof compliance records.

---

## Flow

```text
Loan Request
      |
      v
Decision Generated
      |
      v
Audit Log Created
      |
      v
Stored with Integrity Verification
```

---

# Ticket 03 Analysis

## Problem Statement

Prove the PII-redaction guardrail ran before the model call on all 12,400 approvals last quarter.

---

## Correct Answer

### Both ✅

---

## Why This Answer?

The requirement has two parts.

### Part 1

Need to verify execution order.

```text
Request
   |
PII Redaction
   |
Model Call
   |
Response
```

This requires Trace/Spans.

---

### Part 2

Need compliance evidence proving the guardrail executed.

This requires Audit Logs.

---

## Why Not Trace / Spans Only?

Trace shows execution order but does not provide long-term compliance evidence.

---

## Why Not Audit Log Only?

Audit Logs record events but do not provide detailed request flow and execution timing.

---

## Flow

```text
Request
   |
Guardrail Executed
   |
Model Invoked
   |
Decision Stored

      Trace
        +
    Audit Log
```

---

# Ticket 04 Analysis

## Problem Statement

You're reproducing a single failing request in staging — show the full call tree and pinpoint where it errored.

---

## Correct Answer

### Trace / Spans ✅

---

## Why This Answer?

The objective is debugging.

Requirements:

- Full call tree
- Execution path
- Error location

Trace/Spans provide detailed visibility into request execution.

---

## Example

```text
API Gateway
     |
Authentication
     |
Retrieval Service
     |
LLM Call
     |
ERROR
```

Trace immediately identifies the failing component.

---

## Why Not Audit Log?

Audit Logs store actions and decisions but do not show detailed execution trees.

---

## Flow

```text
Request
   |
Service A
   |
Service B
   |
Service C
   |
Error Detected
```

---

# Ticket 05 Analysis

## Problem Statement

FinOps wants average cost and tokens per request on a live dashboard. Sampling 10% is fine.

---

## Correct Answer

### Trace / Spans ✅

---

## Why This Answer?

Keywords:

- Average cost
- Token usage
- Dashboard
- Sampling acceptable

Trace systems are designed for metrics collection and operational monitoring.

Sampling is commonly used in observability systems.

---

## Example

```text
Request 1 = 1000 Tokens

Request 2 = 1500 Tokens

Request 3 = 1200 Tokens

Average = 1233 Tokens
```

---

## Why Not Audit Log?

Audit Logs are designed for complete and permanent records.

They are not optimized for dashboard analytics and sampled telemetry.

---

## Flow

```text
Requests
     |
Token Collection
     |
Cost Calculation
     |
Dashboard Metrics
```

---

# Ticket 06 Analysis

## Problem Statement

This decision record must survive even a DBA with write access trying to alter it three years from now.

---

## Correct Answer

### Audit Log ✅

---

## Why This Answer?

The requirement focuses on:

- Long-term storage
- Tamper resistance
- Security
- Integrity verification

Audit Logs are append-only and often hash-chained.

---

## Example

```text
Record A
   |
Hash
   |
Record B
   |
Hash
   |
Record C
```

If Record B is modified:

```text
Hash Validation Failed
```

Tampering becomes immediately visible.

---

## Why Not Trace / Spans?

Trace data is usually:

- Temporary
- Sampled
- Used for debugging

It is not designed for long-term compliance evidence.

---

## Flow

```text
Decision Created
      |
Audit Record Generated
      |
Hash Chained
      |
Stored Securely
      |
Verified Years Later
```

---

# Ticket 08 Analysis

## Problem Statement

A guardrail blocked a suspicious transaction.

Compliance needs a permanent record that it was blocked.

On-call needs to debug why it fired on a legitimate-looking request.

---

## Correct Answer

### Both ✅

---

## Why This Answer?

Two independent requirements exist.

### Requirement 1

Compliance requires:

- Permanent record
- Audit evidence
- Proof of blocking

This requires Audit Logs.

---

### Requirement 2

Operations team requires:

- Debugging
- Root cause analysis
- Guardrail investigation

This requires Trace/Spans.

---

## Why Not Trace Only?

Trace provides debugging but does not provide permanent compliance records.

---

## Why Not Audit Log Only?

Audit Logs provide proof but cannot explain detailed execution behavior.

---

## Flow

```text
Request
    |
Guardrail
    |
Blocked
    |
-----------------------
|                     |
v                     v

Trace           Audit Log

Why Fired?      Proof Stored
Debugging       Compliance
```

---

# Comparison Table

| Ticket | Correct Answer | Reason |
|----------|----------|----------|
| Ticket 02 | Audit Log | Accountability and proof of integrity |
| Ticket 03 | Both | Execution sequence + compliance evidence |
| Ticket 04 | Trace/Spans | Debugging and error identification |
| Ticket 05 | Trace/Spans | Cost metrics, tokens, dashboard analytics |
| Ticket 06 | Audit Log | Long-term tamper-proof records |
| Ticket 08 | Both | Compliance evidence and debugging requirements |

---

# Quick Decision Guide

## Use Trace / Spans When

- Finding errors
- Measuring latency
- Debugging requests
- Viewing service dependencies
- Monitoring performance
- Tracking token usage and costs

Questions usually contain:

- Where?
- Why slow?
- Which service failed?
- How long?

---

## Use Audit Logs When

- Proving actions occurred
- Compliance reviews
- Regulatory audits
- Security investigations
- Decision tracking
- Tamper detection

Questions usually contain:

- Who?
- What decision?
- Which model version?
- Prove it?
- Was it altered?

---

## Use Both When

The problem requires:

- Operational visibility
- Compliance evidence

at the same time.

Examples:

- Guardrail execution verification
- Blocked transaction investigation
- Compliance + debugging scenarios

---

# Conclusion

Trace/Spans and Audit Logs solve different problems.

Trace/Spans focus on observability and operational troubleshooting by showing request flows, latency, and failures.

Audit Logs focus on governance and compliance by providing permanent, verifiable, and tamper-resistant records of important decisions and actions.

When both operational insight and regulatory proof are required, Trace/Spans and Audit Logs must work together using a common identifier to correlate system activity with audit evidence.