"""
Simple test script for the Training CLI application.
"""
import subprocess
import sys

def run_command(command):
    """Run a command and print the output."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    print("Output:")
    print(result.stdout)
    if result.stderr:
        print("Error:")
        print(result.stderr)
    print("-" * 50)
    return result

def main():
    """Run basic tests for the Training CLI application."""
    # Test help command
    run_command("training --help")
    
    # Test add command help
    run_command("training add --help")
    
    # Test goal command help
    run_command("training goal --help")
    
    # Test list command help
    run_command("training list --help")
    
    # Test clear command help
    run_command("training clear --help")
    
    # Test graph command help
    run_command("training graph --help")
    
    print("All tests completed.")

if __name__ == "__main__":
    main()