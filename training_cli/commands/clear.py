"""
Clear command for the Training CLI application.
Allows clearing exercise data.
"""
import click
import os
from training_cli.utils.data import DATA_FILE, load_data, save_data

@click.command()
@click.option("--all", "clear_all", is_flag=True, help="Clear all data including exercise types and goals.")
@click.option("--date", "-d", help="Clear entries for a specific date (YYYY-MM-DD).")
@click.option("--exercise", "-e", help="Clear entries for a specific exercise type.")
@click.option("--goals", is_flag=True, help="Clear all goals.")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt.")
def clear(clear_all, date, exercise, goals, force):
    """Clear exercise data."""
    # Load current data
    data = load_data()
    
    # Handle clearing all data
    if clear_all:
        if not force and not click.confirm("Are you sure you want to clear ALL data? This cannot be undone.", default=False):
            click.echo("Operation cancelled.")
            return
        
        # Delete the data file
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
            click.echo("All data has been cleared.")
        else:
            click.echo("No data file found.")
        return
    
    # Handle clearing goals
    if goals:
        if not force and not click.confirm("Are you sure you want to clear all goals?", default=False):
            click.echo("Operation cancelled.")
            return
        
        data["goals"] = {}
        save_data(data)
        click.echo("All goals have been cleared.")
        return
    
    # Handle clearing entries for a specific date
    if date:
        if date in data["entries"]:
            if exercise:
                # Clear only entries for the specified exercise on the specified date
                if not force and not click.confirm(f"Are you sure you want to clear all '{exercise}' entries for {date}?", default=False):
                    click.echo("Operation cancelled.")
                    return
                
                # Filter out entries for the specified exercise
                data["entries"][date] = [
                    entry for entry in data["entries"][date]
                    if entry["exercise_type"].lower() != exercise.lower()
                ]
                
                # Remove the date entry if it's empty
                if not data["entries"][date]:
                    del data["entries"][date]
                
                save_data(data)
                click.echo(f"Cleared all '{exercise}' entries for {date}.")
            else:
                # Clear all entries for the specified date
                if not force and not click.confirm(f"Are you sure you want to clear all entries for {date}?", default=False):
                    click.echo("Operation cancelled.")
                    return
                
                del data["entries"][date]
                save_data(data)
                click.echo(f"Cleared all entries for {date}.")
        else:
            click.echo(f"No entries found for {date}.")
        return
    
    # Handle clearing entries for a specific exercise type
    if exercise:
        if not force and not click.confirm(f"Are you sure you want to clear all entries for '{exercise}'?", default=False):
            click.echo("Operation cancelled.")
            return
        
        # Filter out entries for the specified exercise from all dates
        modified = False
        for date in list(data["entries"].keys()):
            original_count = len(data["entries"][date])
            data["entries"][date] = [
                entry for entry in data["entries"][date]
                if entry["exercise_type"].lower() != exercise.lower()
            ]
            
            # Remove the date entry if it's empty
            if not data["entries"][date]:
                del data["entries"][date]
            
            if len(data["entries"].get(date, [])) != original_count:
                modified = True
        
        if modified:
            save_data(data)
            click.echo(f"Cleared all entries for '{exercise}'.")
        else:
            click.echo(f"No entries found for '{exercise}'.")
        return
    
    # If no specific options were provided, clear all entries
    if not force and not click.confirm("Are you sure you want to clear all exercise entries? Goals and exercise types will be preserved.", default=False):
        click.echo("Operation cancelled.")
        return
    
    data["entries"] = {}
    save_data(data)
    click.echo("All exercise entries have been cleared.")