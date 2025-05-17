"""
Training CLI - A command-line tool for tracking exercise activities.
"""
import click

@click.group()
def cli():
    """Training CLI - A command-line tool for tracking exercise activities."""
    pass

# Import and register commands
from training_cli.commands.add import add
from training_cli.commands.goal import goal
from training_cli.commands.list import list_exercises
from training_cli.commands.clear import clear
from training_cli.commands.graph import graph

# Register commands
cli.add_command(add)
cli.add_command(goal)
cli.add_command(list_exercises)
cli.add_command(clear)
cli.add_command(graph)

if __name__ == "__main__":
    cli()