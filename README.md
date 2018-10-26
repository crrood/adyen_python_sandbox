# adyen_python_sandbox
Snippets of code to communicate with the test Adyen payments server

## Setup:
Download the source code to your local computer and enter the directory:
```shell
git clone https://github.com/crrood/adyen_python_sandbox.git
cd adyen_python_sandbox
```
Add authentication credentials to config.ini.  See example_config.ini for file format.

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

Then go to [localhost:8000](http://localhost:8000) in your browser to view a list of integrations.