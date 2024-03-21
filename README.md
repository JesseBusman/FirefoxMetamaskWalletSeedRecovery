# Unfortunately this is not guaranteed to work for you

This may not work for every version of Firefox and/or Metamask.

This only works if you know the password of your wallet.

This only works if you can still have the data folder of the Firefox installation that held your wallet.

# How to use
1. Make sure you have Python 3 installed
2. Install the python packages `python-snappy` and `python-cramjam`
3. Browse to your Firefox data folder (you may need to show hidden files)

   On Windows it's likely to be here: `C:\Users\[USERNAME]\AppData\Roaming\Mozilla`

   On Linux it's likely to be here: `/home/[USERNAME]/.mozilla`
   
4. Download this repository's script:
   
   https://raw.githubusercontent.com/JesseBusman/FirefoxMetamaskWalletSeedRecovery/main/firefox_metamask_seed_recovery.py
   
   ... and put it in the Firefox folder

5. Open a terminal, command prompt or powershell in the Firefox folder
   
   On Windows: Shift + Right Click on the Firefox folder -> Open command prompt or PowerShell here

6. Run this command: `python firefox_metamask_seed_recovery.py`

7. If successful, something like this will be displayed:

   ```
   ---------------------------------------
   Probably found a Metamask vault:

   {"data":"m9b27bSJDFv5svrd7r76v/98nnv678b4TG6v8m+k0v998vnFf98nvfd9f==","iv":"8bbsvdG/G453==","salt":"AS6D/faas+8JJSD="}

   ---------------------------------------
   ```

8. Copy everything from the `{` up to and including the `}`. Metamask calls this the 'vault data'

   On Windows: Click and drag to select, then press Enter to copy

9. You can now use the Vault Decryptor: https://metamask.github.io/vault-decryptor/

   - Download these two files and save them in the same folder:
     
     https://raw.githubusercontent.com/MetaMask/vault-decryptor/master/index.html

     https://raw.githubusercontent.com/MetaMask/vault-decryptor/master/bundle.js
     
   - Recommended: Disconnect your computer from the internet
   - Open the `index.html` you downloaded and use it to recover your wallet seed
   - When finished, close the Vault Decryptor browser tab and delete the `index.html` and `bundle.js` files
   - You may now reconnect to the internet

   If the vault decryptor gives you a 'Problem decoding vault' error, try using an older version of the vault decryptor by downloading these two files instead:
     
     https://raw.githubusercontent.com/MetaMask/vault-decryptor/186101b5d7047aabc2d04455bbaa103f9f3c425a/index.html
     
     https://raw.githubusercontent.com/MetaMask/vault-decryptor/186101b5d7047aabc2d04455bbaa103f9f3c425a/bundle.js

Good luck!

Tips: `0xC5e9aCcd70FaEdafbe28D8b83DCCf5d3E9C8E527`
