##This project is no longer being maintained, please see [this repo](https://github.com/crrood/adyen_integration_samples) for up to date samples

# adyen_python_sandbox
Code samples for (almost) all of the available Adyen integrations, meant as a reference for an end-to-end implementation.

## Setup:
Download the source code to your local computer:
```bash
git clone https://github.com/crrood/adyen_python_sandbox.git
```
Add authentication credentials to `config.ini`.  See `example_config.ini` for file format:
```
[credentials]  # static
merchantAccount = [Your merchant account]
apiKey = [Your webservice user API key]
wsUser = [Your webservice user name]
wsPass = [Your webservice user password]
skinCode = [SkinCode for your HPP skin]  # only for deprecated HPP integration
hmacKey = [HMAC key for your HPP skin]  # only for deprecated HPP integration
```

To use any Adyen front-end library, change the value of ORIGIN_KEY in scripts/common.js to the value generated on your webservice user per the below:
https://docs.adyen.com/user-management/how-to-get-an-origin-key

Finally, make sure python3 is in your path and run `./update_python_path` to configure the server.  

## Start
From the base directory, start a server with the supplied script:
```bash
./start_server.sh
```

Then go to [localhost:8000](http://localhost:8000) in your browser to view a list of integrations.

## Issues
I'll do my best to keep everything running, but things will inevitably get out of date.  Please open an issue or pull request if you notice any problems.
