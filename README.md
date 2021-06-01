## Installation

Clone the [source repository](https://github.com/samitkk18/cowin-alert) from Github.
```sh
$ git clone https://github.com/samitkk18/cowin-alert.git
```
Install the required python libraries from `requirements.txt` file.
```sh
$ pip install -r requirements.txt 
```

## Usage

Once installed, this is very easy to use. First, change the configurations in the `config.yml` file according to your need.

Then simply run the main.py file:
It does 2 steps: create sqlite3 database and email_alerts
```sh
$ python main.py
```


## Use Cases

1. use `email_alerts` to send vaccine availability alerts periodically by automating the script with Crontab or task scheduler in case of windows.

## Acknowledgements

- [Co-WIN Public APIs](https://apisetu.gov.in/public/marketplace/api/cowin/cowin-public-v2)
