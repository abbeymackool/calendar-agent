import typer
from calendar_agent.sync.run_airbnb import main as airbnb_main
from calendar_agent.sync.run_peerspace import main as peerspace_main
from calendar_agent.sync.run_gmail import main as gmail_main

app = typer.Typer(help="Calendar Agent CLI")

@app.command()
def airbnb():
    airbnb_main()

@app.command()
def peerspace():
    peerspace_main()

@app.command()
def gmail():
    gmail_main()

if __name__ == "__main__":
    app()
