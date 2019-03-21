# adyen_python_sandbox
Code samples for (almost) all of the available Adyen integrations, using vanilla JS and a python CGI backend to run without any external libraries.

## Setup:
Download the source code to your local computer:
```bash
git clone https://github.com/crrood/adyen_python_sandbox.git
```
Add authentication credentials to `config.ini`.  See `example_config.ini` for file format:
```
[credentials] # must be present
merchantAccount = [Your merchant account]
wsUser = [Your webservice user name]
wsPass = [Your webservice user password]
apiKey = [Your webservice user API key]
skinCode = [SkinCode for your HPP skin]
hmacKey = [HMAC key for your HPP skin]
```

## Start
CD to the base directory and start a server with the supplied script:
```bash
./start_server.sh
```

Then go to [localhost:8000](http://localhost:8000) in your browser to view a list of integrations.

## Troubleshooting
If you get a `permission denied... submit.py` error, try
```
./update_python_path
```

If that doesn't solve it, you'll need to manually locate your python3 bin file and add the path to first line of submit.py after the shebang, i.e. 
```
#!/usr/bin/python3
```

## Bugs
I'll do my best to keep everything running, but as the integrations are always changing things might get out of date.  Feel free to reach out via email / mattermost with any problems, or even submit a pull request if you're feeling ambitious :)