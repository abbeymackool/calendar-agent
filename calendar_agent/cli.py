import typer
from calendar_agent.sync import run_airbnb, run_peerspace, run_gmail

app = typer.Typer(help="Calendar Agent CLI")

@app.command()
def airbnb():
    run_airbnb.main()

@app.command()
def peerspace():
    run_peerspace.main()

@app.command()
def gmail():
    run_gmail.main()

if __name__ == "__main__":
    app()
