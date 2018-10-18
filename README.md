# adyen_python_sandbox
Snippets of code to communicate with the test Adyen payments server

## Setup:
Add authentication credentials to credentials.csv in the format:
```
merchantAccount,wsUser,wsPass,apiKey
YourMerchantAccount,ws_xxxxx@Company.YourCompany,YourWebServicePassword,YourCheckoutAPIKey
```
Update file permissions and python path:
```bash
chmod +x start_server.sh
chmod +x update_python_path.sh
./update_python_path.sh
```

## Start
Start a server in the root directory using
```bash
./start_server.sh
```

Then go to [localhost:8000](http://localhost:8000) in your browser