from calendar_agent.models.booking import Booking
from calendar_agent.models.event import CalendarEvent

def calendar_for_space(space: str) -> str:
    from calendar_agent.config import settings
    return settings.google_calendar_disco_id if space=="Disco" else settings.google_calendar_upstairs_id

def booking_to_event(b: Booking) -> CalendarEvent:
    cal_id = calendar_for_space(b.space)
    summary = f"[{b.source.title()}] {b.space} – " + (b.guest_name or b.kind.title())
    description = f"source={b.source} external_id={b.external_id} kind={b.kind}"
    return CalendarEvent(
        uid="",
        summary=summary,
        description=description,
        start=b.start,
        end=b.end,
        calendar_id=cal_id,
        source=b.source,
        source_external_id=b.external_id,
    )
