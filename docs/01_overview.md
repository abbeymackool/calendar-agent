# Calendar Agent — System Overview

**Project:** Calendar Agent  
**Purpose:** Automate calendar synchronization for Loft #129 (“The Disco Loft”) and Loft #225 (“The Upstairs Loft”), managing Airbnb, Peerspace, and Gmail triggers with precise, rule-based logic.

---

## Locations

### Loft #129 — The Disco Loft
- Functions as: **Airbnb**, **event venue**, and **production studio**.
- Connected platforms:
  - **Peerspace:** auto-syncs confirmed bookings directly to Google Calendar.
  - **Airbnb:** manual sync (via Gmail triggers) due to unreliable native integration.

### Loft #225 — The Upstairs Loft
- Functions exclusively as **Airbnb**.
- No buffers needed; only main reservation events are added.

---

## Core Calendars

| Calendar | Purpose |
|-----------|----------|
| **Disco Bookings** | All confirmed reservations, events, and shoots for the Disco Loft. |
| **Upstairs Bookings** | Airbnb reservations for the Upstairs Loft. |
| **Block on Airbnb** | Manual or automated all-day blocks to prevent overlapping Airbnb stays. |

---

## Gmail Integration

All booking-related messages arrive at **hello@discoloft.com**, hosted on Gmail Workspace.  
Labels are nested as: Airbnb/Disco Bookings
Airbnb/Upstairs Bookings
Peerspace/Event Bookings
Peerspace/Photo Bookings
Peerspace/Booking Updates
Peerspace/Cancellations The agent monitors these labels to trigger workflows.

---

## Trigger Sources

| Source | Example Email | Action |
|---------|----------------|--------|
| **Peerspace (Event/Production)** | “Your booking is confirmed with [guest]...” | Add or update events/buffers. |
| **Peerspace Update** | “Your booking with [guest] has been updated.” | Modify existing events and buffers. |
| **Peerspace Cancel** | “Your booking with [guest] was cancelled.” | Delete related events. |
| **Airbnb Confirmed** | “Reservation confirmed - [guest name] arrives [date].” | Add reservation and buffers. |
| **Airbnb Cancelled** | “Canceled: Reservation [code] for [dates].” | Delete related events. |
| **Airbnb Modified (Future)** | Detected via Playwright scraping message threads. | Adjust times if check-in/out changes. |

---

## Design Goals
- Maintain 100% parity between confirmed bookings and calendar events.  
- Never over-block (e.g., full-day “Reserved” from Airbnb).  
- Prevent duplicates but allow legitimate overlaps (Events vs. Photoshoots).  
- Keep all logic transparent and editable via code.

---
