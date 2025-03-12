import subprocess

async def execution_layer(action: str):
    """ Executes the decided action """
    if "fetch_weather" in action:
        result = subprocess.run(["python3", "weather_script.py"], capture_output=True, text=True)
        return result.stdout

    elif "run_sql_query" in action:
        return None

    else:
        return "No matching action found."