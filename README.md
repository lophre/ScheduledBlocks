# LOPHRE fork of ScheduledBlocks

This is simplified version of [Snake Pool's ScheduledBlock](https://github.com/asnakep/ScheduledBlocks).  This version is only providing slot schedule for the current epoch.

I changed a bit the script to feed it's parameters by using environment variables (useful for containerized environments), you will have to configure those to get going:

```
cardano-leaderlog-5f8b7695f5-k6dmt:$ export BLOCKFROST_ID="your_blockfrost_id_here"
cardano-leaderlog-5f8b7695f5-k6dmt:$ export POOL_ID="6aef3925b53d98084e8a9ec0145c1770e7eb57f84cd2d2613bb4c19a"
cardano-leaderlog-5f8b7695f5-k6dmt:$ export POOL_TICKER="LPR"
cardano-leaderlog-5f8b7695f5-k6dmt:$ export VRF_SKEY_PATH='/opt/srv/cfg/vrf.skey'
cardano-leaderlog-5f8b7695f5-k6dmt:$ export LOCAL_TZ="Etc/UTC"
```

You can get all available timezones with the following:

```
Python 3.8.10 (default, Sep 28 2021, 16:10:42)
[GCC 9.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import pytz
>>> pytz.all_timezones
```

The following is the original README.

# ScheduledBlocks

Scheduled Block Checker for Cardano Stakepool Operators

Lightweight and Portable Scheduled Blocks Checker for Next, Current and Previous Epochs.
No cardano-node Required, data is taken from blockfrost.io and armada-alliance.com

Note: This is a reworking of old python script leaderLogs.py 
available on https://github.com/papacarp/pooltool.io.git


## Prerequisites:
- Python 3.8
- pip (Python package installer)
- libsodium library

## Setup:
- clone this repository using git: ``` git clone https://github.com/asnakep/ScheduledBlocks.git ```
- execute inside the newly cloned directory: ```pip install -r requirements.txt   ```  to install all needed python package requirements
- get a project id on blockfrost.io
- make sure you can access your vrf.skey file (you can copy in it a path of your choice) and remember to keep it as read only ``` chmod 400 vrf.skey ```

- Set Variables on lines 23, 27-30 of ScheduledBlocks.py:

### Set your own timezone -----------------------------------------###
local_tz = pytz.timezone('')

### Set These Variables ###
BlockFrostId = ""
PoolId = ""
PoolTicker = ""
VrfKeyFile = ('')
### -------------------------------------------------------------- ###


## Usage:
``` python3 ScheduledBlocks.py ```

## Output: 
- a *console output* with all the slots assigned for next, current and previous Epochs
