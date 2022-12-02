# Databricks notebook source
# DBTITLE 1,Mount Storage Account
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

# COMMAND ----------

# DBTITLE 1,Store File Locations
ratingsFile="dbfs:/mnt/Files/Validated/ratings.csv"
moviesFile="dbfs:/mnt/Files/Validated/movies.csv"

# COMMAND ----------

# DBTITLE 1,List Files in directory
# MAGIC %fs
# MAGIC ls /mnt/Files/Validated

# COMMAND ----------

# DBTITLE 1,Read and create structure of files
# Movies file
from pyspark.sql.types import *
movies_with_genre_schema = StructType(
    [StructField('ID', IntegerType()),
    StructField('title', StringType()),
    StructField('genres', StringType())])

# Schema where we drop the genres
movies_schema = StructType(
    [StructField('ID', IntegerType()),
    StructField('title', StringType())])

# Ratings file
from pyspark.sql.types import *
user_ratings_all_schema = StructType(
    [StructField('userId', IntegerType()),
    StructField('movieId', IntegerType()),
    StructField('rating', DecimalType()),
    StructField('timestamp', StringType())])

# Schema where we drop the timestamp
user_ratings_schema = StructType(
    [StructField('userId', IntegerType()),
    StructField('movieId', IntegerType()),
    StructField('rating', DecimalType())])

# COMMAND ----------

# DBTITLE 1,Working with schema and dataframe
movie_dataframe = sqlContext.read.format('com.databricks.spark.csv').options(header=True, inferSchema=False).schema(movies_schema).load(moviesFile)
movie_with_genre_dataframe = sqlContext.read.format('com.databricks.spark.csv').options(header=True, inferSchema=False).schema(movies_with_genre_schema).load(moviesFile)

rating_dataframe = sqlContext.read.format('com.databricks.spark.csv').options(header=True, inferSchema=False).schema(user_ratings_schema).load(ratingsFile)
rating_with_timestamp_dataframe = sqlContext.read.format('com.databricks.spark.csv').options(header=True, inferSchema=False).schema(user_ratings_all_schema).load(ratingsFile)

# COMMAND ----------

# DBTITLE 1,Inspect data before transformation
movie_with_genre_dataframe.show(4, truncate = False)
movie_dataframe.show(4, truncate = False)

rating_with_timestamp_dataframe.show(4, truncate = False)
rating_dataframe.show(4, truncate = False)

# COMMAND ----------

# DBTITLE 1,Transforming dataframes
from pyspark.sql.functions import split, regexp_extract

# Extracting the year out of the title
movies_with_year_dataframe = movie_dataframe.select('ID', 'title', regexp_extract('title',r'\((\d+)\)', 1).alias('year'))

# COMMAND ----------

# DBTITLE 1,Dataframe after transformation
movies_with_year_dataframe.show(4, truncate = False)
#display(movie_dataframe)

# COMMAND ----------

# DBTITLE 1,Basic aggregation
display(movies_with_year_dataframe.groupBy('year').count().orderBy('count', ascending = False))

# COMMAND ----------

# DBTITLE 1,Caching data for quicker access
rating_dataframe.cache()
movies_with_year_dataframe.cache()

# COMMAND ----------

# DBTITLE 1,Get avg rating per movie
from pyspark.sql import functions as f

movies_with_average_ratings_dataframe = rating_dataframe.groupBy('movieId').agg(f.count(rating_dataframe.rating).alias('count'), f.avg(rating_dataframe.rating).alias('average_rating'))
print('movies_with_average_ratings_dataframe:')
movies_with_average_ratings_dataframe.show(4, truncate = False)

# COMMAND ----------

# DBTITLE 1,Adding movie title to dataset
movie_title_with_average_ratings_dataframe = movies_with_average_ratings_dataframe.join(movie_dataframe, f.col('movieId') == f.col('ID')).drop('ID')
movie_title_with_average_ratings_dataframe.show(4, truncate = False)
