## Setting up an Azure Storage Account for the Plark tournament

We use Azure blob storage to keep:
 * The config json files containing the game configuration.
 * Logfiles from all matches
 * Video files from all games.

We use a "General-purpose v2 account", setup via the [Azure portal](https://portal.azure.com).

Once you have the storage account created, enter its name in the
`AZ_STORAGE_ACCOUNT_NAME` field in `.env`.

You can go then to its "Overview" page on the Azure portal, and click on "Access Keys" on the left panel.  You can then click on "Show keys" and copy/paste one of the keys into the 'AZ_STORAGE_ACCOUNT_KEY` field in `.env`.

To create containers for the config, log, and video files, click on "Containers" in the left panel, and then "+ Container" at the top, to create and name the three containers.  Then you can fill in the names in `.env`.

Finally, in order to be able to view the logfiles and videos via a simple URL, click on those containers in turn in the portal, and click "Change access level" at the top of the screen, and set the "Public access level" to "Blob (anonymous read access for blobs only)".