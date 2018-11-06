# adyen_python_sandbox
Snippets of code to communicate with the test Adyen payments server

## Setup:
Download the source code to your local computer and enter the directory:
```bash
git clone https://github.com/crrood/adyen_python_sandbox.git
cd adyen_python_sandbox
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

Update file permissions:
```
chmod +x start_server.sh
```

## Start
Start a server in the root directory using
```bash
./start_server.sh
```

Then go to [localhost:8000](http://localhost:8000) in your browser to view a list of integrations.

## Troubleshooting
If you get a `permission denied... submit.py` error, try
```
chmod +x update_python_path.sh
./update_python_path
```

If that doesn't solve it, you'll need to manually locate your python3 bin file and add the path to first line of submit.py after the shebang, i.e. 
```
#!/usr/bin/python3
```

## Bugs
I'll do my best to keep everything running, but this is permanent work in progress so I can't guarantee it'll never break.  Feel free to reach out via email / mattermost with any problems.