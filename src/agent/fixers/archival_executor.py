from abc import ABC, abstractmethod

class BaseArchivalExecutor(ABC):
    @abstractmethod
    def execute_archival(self, asset_name: str) -> str:
        pass

class MockSnowflakeExecutor(BaseArchivalExecutor):
    def execute_archival(self, asset_name: str) -> str:
        return f"EXECUTED: ALTER TABLE {asset_name} SET STORAGE_LIFECYCLE_POLICY = COLD;"

class MockDatabricksExecutor(BaseArchivalExecutor):
    def execute_archival(self, asset_name: str) -> str:
        return f"EXECUTED: ALTER TABLE {asset_name} SET TBLPROPERTIES ('delta.storageTier'='ARCHIVE');"

class MockBigQueryExecutor(BaseArchivalExecutor):
    def execute_archival(self, asset_name: str) -> str:
        return f"EXECUTED: bq update --set_long_term_storage_billing=true {asset_name};"

class MockAzureDataLakeExecutor(BaseArchivalExecutor):
    def execute_archival(self, asset_name: str) -> str:
        return f"EXECUTED: az storage blob set-tier --tier Archive --name {asset_name};"

class ArchivalFactory:
    @staticmethod
    def execute(platform: str, asset_name: str) -> str:
        platform = platform.lower()
        if 'snowflake' in platform:
            return MockSnowflakeExecutor().execute_archival(asset_name)
        elif 'databricks' in platform:
            return MockDatabricksExecutor().execute_archival(asset_name)
        elif 'bigquery' in platform:
            return MockBigQueryExecutor().execute_archival(asset_name)
        elif 'azure data lake' in platform or 'adl' in platform:
            return MockAzureDataLakeExecutor().execute_archival(asset_name)
        else:
            return f"EXECUTED: Generic Archival API call for {asset_name}."
