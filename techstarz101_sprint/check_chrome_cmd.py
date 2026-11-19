import subprocess

try:
    out = subprocess.check_output(
        'wmic process where "name=\'chrome.exe\'" get processid,commandline',
        shell=True,
        text=True,
        errors='ignore'
    )
    for line in out.splitlines():
        if 'remote-debugging-port' in line:
            print("FOUND AUTO CHROME:")
            print(line[:300])
except Exception as e:
    print("Error:", e)

