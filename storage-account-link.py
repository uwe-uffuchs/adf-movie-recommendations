# Databricks notebook source
accountName="sastagingfiles"
validatedContainer="validated"
folder="Data"
mountPoint="/mnt/Files/Validated"
loginBaseUrl="https://login.microsoftonline.com/"

# Application Id
appId=dbutils.secrets.get(scope="kvmovierecommendation", key="client-id")
print(appId)

# Application Secret
appSecret=dbutils.secrets.get(scope="kvmovierecommendation", key="movie-application-app-secret")
print(appSecret)

# Tenant Id
tenantId=dbutils.secrets.get(scope="kvmovierecommendation", key="tenant-id")
print(tenantId)

endpoint=loginBaseUrl+tenantId+"/oauth2/token"
source="abfss://"+validatedContainer+"@"+accountName+".dfs.core.windows.net/"+folder
print(source)

# Connecting using SP secret and OAuth
configs={"fs.azure.account.auth.type": "OAuth",
        "fs.azure.account.oauth.provider.type": "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
        "fs.azure.account.oauth2.client.id": appId,
        "fs.azure.account.oauth2.client.secret": appSecret,
        "fs.azure.account.oauth2.client.endpoint": endpoint}

# Mount ADLS Storage to DBFS
# Only mount if not already mounted
if not any(mount.mountPoint==mountPoint for mount in dbutils.fs.mounts()):
    dbutils.fs.mount(
        source=source,
        mount_point=mountPoint,
        extra_configs=configs)
