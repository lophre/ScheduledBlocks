#!/bin/env python3

import requests
import urllib.request
import math
import binascii
import json
import pytz
import hashlib
import re
import readchar
import os
from ctypes import *
from datetime import datetime, timezone
from sys import exit, platform

class col:
    red = '\033[31m'
    green = '\033[92m'
    endcl = '\033[0m'
    bold = '\033[1m'


### Set These Variables ###
#BlockFrostId = "CsdsTOQB4QS2NBXufiT5L2ZBAnHxcfof"
#PoolId = "6aef3925b53d98084e8a9ec0145c1770e7eb57f84cd2d2613bb4c19a"
#PoolTicker = "LPR"
#VrfKeyFile = ('/opt/srv/vrf.skey')

BlockFrostId = os.environ.get('BLOCKFROST_ID')
PoolId = os.environ.get('POOL_ID')
PoolTicker = os.environ.get('POOL_TICKER')
VrfKeyFile = os.environ.get('VRF_SKEY_PATH')
localTz = os.environ.get('LOCAL_TZ')

### -------------------------------------------------------------- ###

local_tz = pytz.timezone(localTz)

### ADA Unicode symbol and Lovelaces removal ###
ada = " \u20B3"
lovelaces = 1000000

### Get Current Epoch from Armada Alliance ###
headers={'content-type': 'application/json'}
CepochParam = requests.get("https://js.adapools.org/global.json", headers=headers)
json_data = CepochParam.json()
Cepoch = CepochParam.json().get("epoch_last")

### User Prompt for specific prev/curr Epochs
print()
print(col.bold + col.green + f'Welcome to ScheduledBlocks for Cardano SPOs. ')
print()

### Get data from blockfrost.io APIs ###

headers = {'content-type': 'application/json', 'project_id': BlockFrostId}

epochParam = requests.get("https://cardano-mainnet.blockfrost.io/api/v0/epochs/"+Cepoch+"/parameters", headers=headers)
json_data = epochParam.json()
epoch = epochParam.json().get("epoch")
eta0 = epochParam.json().get("nonce")

netStakeParam = requests.get("https://cardano-mainnet.blockfrost.io/api/v0/epochs/"+Cepoch, headers=headers)
json_data = netStakeParam.json()
nStake = int(netStakeParam.json().get("active_stake")) / lovelaces
nStake = "{:,}".format(nStake)

poolHistStake = requests.get("https://cardano-mainnet.blockfrost.io/api/v0/pools/"+PoolId+"/history", headers=headers)
json_data = poolHistStake.json()

for i in json_data :
 if i['epoch'] == int(Cepoch) :
  sigma = (i["active_size"])

for i in json_data :
 if i['epoch'] == int(Cepoch) :
  pStake = (i["active_stake"])
  pStake = int(pStake) / lovelaces
  pStake = "{:,}".format(pStake)

print(col.endcl + col.bold + f'Current epoch: ' + col.green + Cepoch + col.endcl) 
print(col.endcl + col.bold + f'Current epoch nonce: ' + col.bold + col.green + eta0 + col.endcl)
print(col.endcl + col.bold + f'Checking SlotLeader Schedules for Stakepool: ' + (col.green + PoolTicker + col.endcl))
print(col.endcl + col.bold + f'Pool Id: ' + (col.green + PoolId + col.endcl))
print(col.endcl + col.bold + f'Network Active Stake in Epoch ' + Cepoch + ": " + col.green + str(nStake) + col.endcl + col.bold + ada + col.endcl) 
print(col.endcl + col.bold + f'Pool Active Stake in Epoch ' + Cepoch + ": " + col.green + str(pStake) + col.endcl + col.bold + ada + col.endcl + "\n")

### Calculate Slots Leader ###

### Opening vrf.skey file ###
with open(VrfKeyFile) as f:
        skey = json.load(f)
        poolVrfSkey = skey['cborHex'][4:]

### Determine libsodium path based on platform ###
libsodium = None
if platform == "linux" or platform == "linux2":
    # Bindings are not avaliable so using ctypes to just force it in for now.
    libsodium = cdll.LoadLibrary("/usr/local/lib/libsodium.so")
elif platform == "darwin":
    # Try both Daedalus' bundled libsodium and a system-wide libsodium path.
    daedalusLibsodiumPath = os.path.join("/Applications", "Daedalus Mainnet.app", "Contents", "MacOS", "libsodium.23.dylib")
    systemLibsodiumPath = os.path.join("/usr", "local", "lib", "libsodium.23.dylib")

    if os.path.exists(daedalusLibsodiumPath):
        libsodium = cdll.LoadLibrary(daedalusLibsodiumPath)
    elif os.path.exists(systemLibsodiumPath):
        libsodium = cdll.LoadLibrary(systemLibsodiumPath)
    else:
        exit(f'Unable to find libsodium, checked the following paths: {", ".join([daedalusLibsodiumPath, systemLibsodiumPath])}')
libsodium.sodium_init()

### Blockchain Genesis Parameters ###
headers = {'content-type': 'application/json', 'project_id': BlockFrostId}
GenesisParam = requests.get("https://cardano-mainnet.blockfrost.io/api/v0/genesis", headers=headers)
json_data = GenesisParam.json()

epochLength = GenesisParam.json().get("epoch_length")
activeSlotCoeff = GenesisParam.json().get("active_slots_coefficient")
slotLength = GenesisParam.json().get("slot_length")

### Epoch211FirstSlot ###
firstShelleySlot = requests.get("https://cardano-mainnet.blockfrost.io/api/v0/blocks/4555184", headers=headers)
json_data = firstShelleySlot.json()
firstSlot = firstShelleySlot.json().get("slot")

### calculate first slot of target epoch ###
firstSlotOfEpoch = (firstSlot) + (epoch - 211)*epochLength

from decimal import *
getcontext().prec = 9
getcontext().rounding = ROUND_HALF_UP

def mkSeed(slot,eta0):

    h = hashlib.blake2b(digest_size=32)
    h.update(bytearray([0,0,0,0,0,0,0,1])) #neutral nonce
    seedLbytes=h.digest()

    h = hashlib.blake2b(digest_size=32)
    h.update(slot.to_bytes(8,byteorder='big') + binascii.unhexlify(eta0))
    slotToSeedBytes = h.digest()

    seed = [x ^ slotToSeedBytes[i] for i,x in enumerate(seedLbytes)]

    return bytes(seed)

def vrfEvalCertified(seed, tpraosCanBeLeaderSignKeyVRF):
    if isinstance(seed, bytes) and isinstance(tpraosCanBeLeaderSignKeyVRF, bytes):
        proof = create_string_buffer(libsodium.crypto_vrf_ietfdraft03_proofbytes())

        libsodium.crypto_vrf_prove(proof, tpraosCanBeLeaderSignKeyVRF,seed, len(seed))

        proofHash = create_string_buffer(libsodium.crypto_vrf_outputbytes())

        libsodium.crypto_vrf_proof_to_hash(proofHash,proof)

        return proofHash.raw

    else:
        print("error.  Feed me bytes")
        exit()

# Determine if our pool is a slot leader for this given slot
# @param slot The slot to check
# @param activeSlotCoeff The activeSlotsCoeff value from protocol params
# @param sigma The controlled stake proportion for the pool
# @param eta0 The epoch nonce value
# @param poolVrfSkey The vrf signing key for the pool

def isSlotLeader(slot,activeSlotCoeff,sigma,eta0,poolVrfSkey):
    seed = mkSeed(slot, eta0)
    tpraosCanBeLeaderSignKeyVRFb = binascii.unhexlify(poolVrfSkey)
    cert=vrfEvalCertified(seed,tpraosCanBeLeaderSignKeyVRFb)
    certNat  = int.from_bytes(cert, byteorder="big", signed=False)
    certNatMax = math.pow(2,512)
    denominator = certNatMax - certNat
    q = certNatMax / denominator
    c = math.log(1.0 - activeSlotCoeff)
    sigmaOfF = math.exp(-sigma * c)
    return q <= sigmaOfF


slotcount=0

for slot in range(firstSlotOfEpoch,epochLength+firstSlotOfEpoch):

    slotLeader = isSlotLeader(slot, activeSlotCoeff, sigma, eta0, poolVrfSkey)

    if slotLeader:
        pass
        timestamp = datetime.fromtimestamp(slot + 1591566291, tz=local_tz)
        slotcount+=1

        print(col.bold + "Leader At Slot: "  + str(slot-firstSlotOfEpoch) + " - Local Time " + str(timestamp.strftime('%Y-%m-%d %H:%M:%S') + " - Scheduled Epoch Blocks: " + str(slotcount)))

if slotcount == 0:
    print(col.bold + "No SlotLeader Schedules Found for Epoch " +str(epoch))
    exit

print("")

