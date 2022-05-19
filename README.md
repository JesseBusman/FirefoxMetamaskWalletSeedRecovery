# Unfortunately this is not guaranteed to work for you

This only works for specific versions of Firefox and/or Metamask.

This only works if you know the password of your wallet.

This only works if you can still access the data belonging to the Firefox installation that held your wallet, specifically the .sqlite file of your Metamask browser extension.

# How to use
1. Make sure you have Python 3 and pip installed
2. Browse to your Firefox data folder (you may need to show hidden files)

   On Windows it's likely to be here: `C:\Users\[USERNAME]\AppData\Roaming\Mozilla`

   On Linux it's likely to be here: `/home/[USERNAME]/.mozilla`
   
3. Download this repository's script:
   
   https://raw.githubusercontent.com/JesseBusman/FirefoxMetamaskWalletSeedRecovery/main/firefox_metamask_seed_recovery.py
   
   ... and put it in the Firefox folder

4. Open a terminal, command prompt or powershell in the Firefox folder
   
   On Windows: Shift + Right Click on the Firefox folder -> Open command prompt or PowerShell here

5. Run this command: `pip install python-snappy`

6. Run this command: `python3 firefox_metamask_seed_recovery.py`

7. If successful, something like this will be displayed:

   ```
   ---------------------------------------
   Probably found a Metamask vault:

   {"data":"m9b27bSJDFv5svrd7r76v/98nnv678b4TG6v8m+k0v998vnFf98nvfd9f==","iv":"8bbsvdG/G453==","salt":"AS6D/faas+8JJSD="}

   ---------------------------------------
   ```

8. Copy everything from the `{` up to and including the `}`. Metmask calls this the 'vault data'

   On Windows: Click and drag to select, then press Enter to copy

9. You can now use the Vault Decryptor: https://metamask.github.io/vault-decryptor/

   It is recommended to use the Vault Decryptor offline:
   - On the Vault Decryptor web page, press Ctrl + S to download the page
   - Disconnect your computer from the internet
   - Open the locally saved page (`MetaMask Vault Decryptor.html`) and use it to recover your wallet seed
   - When finished, close the Vault Decryptor browser tab and delete the `MetaMask Vault Decryptor.html` file
   - You may now reconnect to the internet

Good luck!

Tips: `0xC5e9aCcd70FaEdafbe28D8b83DCCf5d3E9C8E527`
