# users-drives-items-counter

The repo contains Python script that uses the Microsoft Graph Python SDK to count all items in all drives of all users in the organization.

## Prerequisites

Install python modules by **pip**:

```
pip install msgraph-sdk
pip install azure-identity
```

Register a new application in the [Azure portal](https://portal.azure.com/). Add and grant the Microsoft Graph API application permissions `Files.Read.All` and `User.Read.All`.

## Run the script

Run the script with the following command:

```
python files_count.py
```