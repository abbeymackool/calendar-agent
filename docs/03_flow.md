# Calendar Agent — Flow Diagram

A visual overview of system logic and event propagation.

```mermaid
flowchart TD

%% EMAIL TRIGGERS
A1[Peerspace Email: Event Booking] --> B1[Parse Details → Booking Object]
A2[Peerspace Email: Photo Booking] --> B1
A3[Peerspace Email: Update/Cancel] --> B2[Modify/Delete Events]
A4[Airbnb Email: Reservation] --> B3[Parse Details → Booking Object]
A5[Airbnb Email: Cancel] --> B4[Delete Events]
A6[Airbnb Email: Update (future)] --> B5[Playwright Scraper]

%% PEERSPACE FLOW
B1 --> C1[Create Buffers on Disco Bookings]
C1 --> C2[Evaluate Date Overlap Rules]
C2 --> C3[Create/Update Block(s) on Airbnb Calendar]

%% AIRBNB FLOW
B3 --> D1[Determine Target: Disco or Upstairs]
D1 -->|Disco| D2[Create 3 Events: Buffer, Reservation, Turnover]
D1 -->|Upstairs| D3[Create 1 Event: Reservation Only]

%% UPDATE FLOW
B2 --> C4[Adjust Buffers/Blocks in Place]
B4 --> E1[Remove Related Buffers and Blocks]
B5 --> E2[Modify Events Based on New Itinerary (Future)]

%% OUTPUT
C3 --> F1[Summarize Counts → CLI Output]
D2 --> F1
D3 --> F1
E1 --> F1
E2 --> F1

F1 --> G1[Google Calendar Updated + Logs Written]
---

### 5) (Optional but nice) `/docs/README.md` index
```bash
cat > docs/README.md <<'MD'
# Calendar Agent — Documentation

- **Overview:** [`01_overview.md`](./01_overview.md)
- **Functional Spec:** [`02_functional_spec.md`](./02_functional_spec.md)
- **Flow Diagram:** [`03_flow.md`](./03_flow.md)

Tip: GitHub renders the Mermaid flow chart in `03_flow.md` automatically.
