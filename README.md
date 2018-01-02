# adyen_python_sandbox
Snippets of code to communicate with the Adyen payments server

Can be run locally or on Heroku

## Setup:
Add authentication credentials to /cgi-bin/submit.py

## Start
Start a server in the root directory using
```shell
python3 -m http.server --cgi 8000
```

or

```shell
chmod +x start_server.sh  # first time only
./start_server.sh
```

Then go to localhost:8000 in your browser

## Troubleshooting
If you get permission problems, run
```shell
chmod +x cgi-bin/submit.py
```