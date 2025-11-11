from calendar_agent.calendar.google import create as gcreate, update as gupdate


def create(event):
    return gcreate(event)


def update(provider_id, event):
    return gupdate(provider_id, event)


def main():
    return
