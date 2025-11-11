# Functional Specification — Calendar Agent

This document defines all functional rules, trigger conditions, and automation logic.

---

## 1. Peerspace Logic

### 1.1. Peerspace → Disco Bookings
- The Peerspace → Google Calendar integration already creates the main event automatically.
- The agent **adds buffer and blocking events** around that booking.

#### a. Event Bookings
- **Trigger:** Gmail label `Peerspace/Event Bookings`.
- **Main calendar:** Disco Bookings.
- **Rule:**  
  - Create an event starting **1 hour before** and ending **2 hours after** the confirmed timeframe.  
  - Title: `EVENT`.  
  - Location: `1-hr buffer`.
- **Also:**  
  - Add **all-day block(s)** on the “Block on Airbnb” calendar for affected dates.
  - The logic determines which days to block based on check-in/out overlaps.

#### b. Photo Bookings
- **Trigger:** Gmail label `Peerspace/Photo Bookings`.
- **Main calendar:** Disco Bookings.
- **Rule:**  
  - Create an event starting **1 hour before** and ending **1 hour after** the confirmed timeframe.  
  - Title: `PHOTOSHOOT`.  
  - Location: `1-hr buffer`.
- **Also:**  
  - Add all-day block(s) to “Block on Airbnb” based on overlap rules.

---

### 1.2. Block Logic for Peerspace Bookings

| Condition | Dates to Block on Airbnb |
|------------|--------------------------|
| Booking ends before 1 PM | Block the **previous day only** |
| Booking ends after 1 PM | Block both the **previous day** and **same day** |
| Booking starts early (< 11 AM) | Block the **previous day**, labeled **AM EVENT** or **AM PHOTOSHOOT** |
| Multiple blocks on same date | Merge names → e.g., “EVENT + SHOOT”, “2X SHOOTS”, “Event + 2x Shoots” |

- If a block event already exists for a given date, the name should be updated, not duplicated.

---

### 1.3. Peerspace Updates
- **Trigger:** Gmail label `Peerspace/Booking Updates`.
- **Action:** Modify buffer or block events according to the new timeframe.  
  - Update event start/end instead of deleting and recreating when possible.
  - Ignore updates that only affect payment.

---

### 1.4. Peerspace Cancellations
- **Trigger:** Gmail label `Peerspace/Cancellations`.
- **Action:** Delete the related buffer and block events for the canceled booking.

---

## 2. Airbnb Logic

### 2.1. Airbnb → Disco or Upstairs
- **Trigger:** Gmail labels:
  - `Airbnb/Disco Bookings`
  - `Airbnb/Upstairs Bookings`
- **Rules:**
  1. Create reservation event on appropriate calendar titled with guest name.  
     - Start = Check-in (usually 4 PM)  
     - End = Checkout (usually 11 AM)
  2. **Disco Loft only:**
     - Add `CHECK-IN BUFFER` (−2h → check-in)
     - Add `TURNOVER` (checkout → +2h)
  3. **Upstairs Loft:** reservation only (no buffers).

### 2.2. Airbnb Cancellations
- **Trigger:** Gmail label `Airbnb/Cancellations`.
- **Action:** Delete all three associated events (buffer, reservation, turnover).

### 2.3. Airbnb Updates (Future Phase)
- Email-based updates are insufficient.  
- Future agent behavior:
  - Use **Playwright integration** with Airbnb message threads.
  - Scrape modified check-in/out times from the guest itinerary.
  - Update existing events in place.

---

## 3. Email Handling + Gmail Labels

| Label | Purpose | Calendar Affected |
|--------|----------|------------------|
| `Peerspace/Event Bookings` | Confirmed events | Disco Bookings, Block on Airbnb |
| `Peerspace/Photo Bookings` | Confirmed photoshoots | Disco Bookings, Block on Airbnb |
| `Peerspace/Booking Updates` | Updated timeframes | Disco Bookings, Block on Airbnb |
| `Peerspace/Cancellations` | Cancellations | Disco Bookings, Block on Airbnb |
| `Airbnb/Disco Bookings` | Confirmed stays | Disco Bookings |
| `Airbnb/Upstairs Bookings` | Confirmed stays | Upstairs Bookings |
| `Airbnb/Cancellations` | Cancelled stays | Disco + Upstairs |

---

## 4. Environment + Config Variables

| Key | Description |
|------|--------------|
| `GOOGLE_CREDENTIALS_FILE` | Path to credentials JSON |
| `GOOGLE_TOKEN_FILE` | Path to OAuth token |
| `CAL_DISCO_BOOKINGS` | Calendar ID for Disco Bookings |
| `CAL_UPSTAIRS_BOOKINGS` | Calendar ID for Upstairs Bookings |
| `CAL_BLOCK_ON_AIRBNB` | Calendar ID for Block on Airbnb |
| `LOG_LEVEL` | Logging verbosity |

---

## 5. Future Additions
- Idempotency (prevent duplicate event creation).
- Dry-run mode (`--dry-run` flag for testing logic).
- Airbnb itinerary scraping (Playwright + OpenAI AgentKit).
