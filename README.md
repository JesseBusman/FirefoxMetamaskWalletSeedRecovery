This only works if you know the password and can still access the .sqlite file belonging to the Metamask installation that had your wallet.

# How to use
1. Have basic knowledge of how to use a terminal/command prompt and how to run python scripts
2. `pip install snappy`
3. `pip install python-snappy`
4. Find your Metamask extension's data folder. The folder name contains the ID of the Firefox Metamask extension: 9f4870ed-b576-47fa-bbd6-0172425975d4

   On Windows it's likely to be in this folder: C:\Users\[USERNAME]\AppData\Roaming\Mozilla\Firefox

   On Linux it's likely to be in this folder: /home/[USERNAME]/.mozilla/firefox
5. Find the .sqlite file inside this folder structure
6. `python3 firefox_metamask_seed_recovery.py yourmetamaskdata.sqlite`

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
