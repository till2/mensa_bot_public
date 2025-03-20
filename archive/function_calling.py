import subprocess

def ls(path):
    try:
        result = subprocess.run(['ls', path], capture_output=True, text=True, check=True).stdout
        if len(result) > 200:
            result = result[:200] + "\n(Info: Result was trimmed off after 200 characters.)"
        return result
    except Exception as e:
        return f"Empty directory (or the function returned an error)."

def findfile(path, filename):
    try:
        result = subprocess.run(['find', path, '-name', filename.strip()], capture_output=True, text=True, check=True).stdout.strip()
        if len(result) > 200:
            result = result[:200] + "\n(Info: Result was trimmed off after 200 characters.)"
        return result
    except Exception as e:
        return f"There were no results (or the function returned an error)."

def findregex(path, regex):
    try:
        result = subprocess.run(['find', path, '-name', regex.strip()], capture_output=True, text=True, check=True).stdout.strip()
        if len(result) > 200:
            result = result[:200] + "\n(Info: Result was trimmed off after 200 characters.)"
        return result
    except Exception as e:
        return f"There were no results (or the function returned an error)." # capture_output=True, text=True, check=True