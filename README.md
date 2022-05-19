This only works if you know the password and can still access the data belonging to the Firefox installation that held your wallet.

# How to use
1. Have basic knowledge of how to use a terminal/command prompt and how to run python scripts
2. `pip install python-snappy` (you may need to `sudo` or run console as administrator)
3. Find your Firefox data folder and `cd` into it

   On Windows it's likely to be here: `C:\Users\[USERNAME]\AppData\Roaming\Mozilla\Firefox`

   On Linux it's likely to be here: `/home/[USERNAME]/.mozilla/firefox`
4. Download and run this repository's script: `python3 firefox_metamask_seed_recovery.py`

If successful, something like this will be printed:

```
---------------------------------------
Probably found a Metamask vault:

{"data":"m9b27bSJDFv5svrd7r76v/98nnv678b4TG6v8m+k0v998vnFf98nvfd9f==","iv":"8bbsvdG/G453==","salt":"AS6D/faas+8JJSD="}

---------------------------------------
```

Copy everything from the `{` up to and including the `}`

You can now use the Vault Decryptor: https://metamask.github.io/vault-decryptor/

Good luck!

Tips: `0xC5e9aCcd70FaEdafbe28D8b83DCCf5d3E9C8E527`
