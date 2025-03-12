import subprocess

async def execution_layer(action: str):
    """ Executes the decided action """
    if "calibrate_cellink_x6" in action:
        result = subprocess.run(["python3", "calibration_x6.py"], capture_output=True, text=True)
        return result.stdout

    elif "run_sql_query" in action:
        # Example: Run a dummy SQL query (replace with actual DB connection)
        return "Executed SQL query successfully."

    else:
        return "No matching action found."