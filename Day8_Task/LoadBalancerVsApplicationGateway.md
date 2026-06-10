# Healthcare Traffic Routing Design
# Application Gateway vs Load Balancer

## Introduction

In a healthcare environment, different applications have different networking requirements. Some services require advanced security, URL inspection, and HTTPS handling, while others need fast TCP traffic distribution and high availability.

This document explains the recommended Azure networking component (**Application Gateway** or **Load Balancer**) for each healthcare service along with the reasoning and traffic flow.

---

# 1. Patient Web Portal

## Selected Component
**Application Gateway**

## Description

The Patient Web Portal is a public-facing web application that allows patients to:

- Book appointments
- View medical reports
- Check billing information
- Access healthcare services online

Since the application is exposed to the internet, security is critical.

## Why Application Gateway?

Application Gateway operates at **Layer 7 (Application Layer)** and can understand HTTP/HTTPS traffic.

### Key Benefits

- Supports HTTPS traffic
- Provides Web Application Firewall (WAF)
- Performs SSL/TLS termination
- Supports URL-based routing
- Protects against web attacks such as SQL Injection and XSS

## Traffic Flow

```text
Patient Browser
       │
       │ HTTPS Request
       ▼
┌──────────────────────┐
│ Application Gateway  │
│        + WAF         │
└──────────┬───────────┘
           │
     URL Inspection
           │
 ┌─────────┼─────────┐
 ▼         ▼         ▼
Appointments Reports Billing
 Service      Service   Service
```

## Decision

Application Gateway is selected because the portal requires secure internet access, URL routing, and web application protection.

---

# 2. Clinical API (Internal)

## Selected Component
**Load Balancer**

## Description

The Clinical API is used internally by hospital systems to exchange patient and clinical data.

The primary requirement is reliable traffic distribution among multiple API servers.

## Why Load Balancer?

Load Balancer operates at **Layer 4 (Transport Layer)** and efficiently distributes TCP traffic without inspecting packet content.

### Key Benefits

- High availability
- Internal traffic distribution
- Fast Layer 4 routing
- Low latency
- Efficient TCP load balancing

## Traffic Flow

```text
Hospital Applications
         │
         │ TCP Requests
         ▼
 ┌──────────────────┐
 │  Load Balancer   │
 └────────┬─────────┘
          │
    ┌─────┼─────┐
    ▼     ▼     ▼
  API1  API2  API3
```

## Decision

Load Balancer is selected because only traffic distribution and failover are required, not application-level inspection.

---

# 3. DICOM Image Streaming

## Selected Component
**Load Balancer**

## Description

DICOM is the standard protocol used for transferring medical images such as:

- MRI scans
- CT scans
- X-Ray images
- Ultrasound images

These files are extremely large and require long-running network connections.

## Why Load Balancer?

The workload is network-intensive and does not require HTTP inspection.

### Key Benefits

- Handles large TCP payloads
- Supports long-lived connections
- High throughput
- Better performance for large file transfers

## Traffic Flow

```text
MRI / CT Scanner
        │
        │ DICOM Stream
        ▼
 ┌──────────────────┐
 │  Load Balancer   │
 └────────┬─────────┘
          │
   ┌──────┼──────┐
   ▼      ▼      ▼
Storage1 Storage2 Storage3
```

## Decision

Load Balancer is selected because image streaming requires maximum throughput and efficient TCP handling.

---

# 4. Authentication Service

## Selected Component
**Application Gateway**

## Description

The Authentication Service validates users before granting access to healthcare applications.

Authentication requests often contain:

- Authorization headers
- Cookies
- JWT Tokens
- Session information

## Why Application Gateway?

Application Gateway can inspect HTTP headers and route traffic intelligently.

### Key Benefits

- Header-based routing
- HTTPS handling
- Layer 7 inspection
- Improved security
- Token-aware routing

## Traffic Flow

```text
User Login Request
         │
         │ HTTPS
         ▼
┌──────────────────────┐
│ Application Gateway  │
└──────────┬───────────┘
           │
    Header Inspection
           │
           ▼
 Authentication Service
```

## Decision

Application Gateway is selected because authentication requires inspection of request headers and secure HTTPS processing.

---

# 5. Legacy SOAP Lab Service

## Selected Component
**Load Balancer**

## Description

The laboratory system uses a legacy SOAP service for communication between internal healthcare applications.

The service mainly requires:

- High availability
- Failover support
- Reliable traffic distribution

## Why Load Balancer?

SOAP traffic does not require advanced routing rules or application-layer inspection.

### Key Benefits

- TCP traffic handling
- Automatic failover
- High availability
- Simple load distribution

## Traffic Flow

```text
Laboratory Systems
         │
         │ SOAP Requests
         ▼
 ┌──────────────────┐
 │  Load Balancer   │
 └────────┬─────────┘
          │
      ┌───┴───┐
      ▼       ▼
   SOAP1   SOAP2
```

## Decision

Load Balancer is selected because the primary requirement is failover and traffic distribution.

---

# 6. Admin Dashboard

## Selected Component
**Application Gateway**

## Description

The Admin Dashboard is a web-based platform used by administrators to manage healthcare operations.

It often hosts multiple services under different hostnames.

## Why Application Gateway?

Application Gateway supports hostname-based routing and advanced web security.

### Key Benefits

- HTTPS support
- SSL/TLS termination
- Hostname-based routing
- Web Application Firewall (WAF)
- Layer 7 routing

## Traffic Flow

```text
Administrator
      │
      │ HTTPS
      ▼
┌──────────────────────┐
│ Application Gateway  │
└──────────┬───────────┘
           │
    Hostname Routing
           │
 ┌─────────┼─────────┐
 ▼         ▼         ▼
Admin    Reports    Audit
Portal   Portal     Portal
```

## Decision

Application Gateway is selected because the dashboard requires secure web access and hostname-based routing.

---

# Overall Healthcare Architecture

```text
                         INTERNET
                              │
                              ▼
                ┌─────────────────────────┐
                │   Application Gateway   │
                │      (Layer 7)          │
                └───────────┬─────────────┘
                            │
      ┌─────────────────────┼─────────────────────┐
      ▼                     ▼                     ▼
 Patient Portal    Authentication Service   Admin Dashboard


                    INTERNAL HOSPITAL NETWORK
                              │
                              ▼
                    ┌─────────────────┐
                    │ Load Balancer   │
                    │   (Layer 4)     │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
   Clinical API      DICOM Streaming      SOAP Lab Service
```

---

# Summary Table

| Requirement | Selected Component | Main Reason |
|------------|-------------------|-------------|
| Patient Web Portal | Application Gateway | HTTPS, WAF, URL Routing |
| Clinical API | Load Balancer | Internal TCP Traffic |
| DICOM Image Streaming | Load Balancer | Large Payload Transfer |
| Authentication Service | Application Gateway | Header Inspection |
| SOAP Lab Service | Load Balancer | TCP Failover |
| Admin Dashboard | Application Gateway | Hostname-Based Routing |

---

# Conclusion

The healthcare platform uses both **Application Gateway** and **Load Balancer** because each service has unique requirements.

### Application Gateway is used when:
- HTTPS traffic is involved
- Security inspection is required
- URL/Header/Hostname routing is needed
- WAF protection is required

### Load Balancer is used when:
- Fast TCP traffic distribution is required
- Large data transfers occur
- Internal communication is needed
- High availability and failover are the primary goals

This architecture ensures a secure, scalable, and highly available healthcare platform.