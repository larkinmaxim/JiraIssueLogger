"""
BigQuery Schema Module

This module defines the schema for the BigQuery tables used in the Jira Logger application.
"""

from google.cloud import bigquery


# Define the schema for the jira_issues table
JIRA_ISSUES_SCHEMA = [
    bigquery.SchemaField("issue_key", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("summary", "STRING"),
    bigquery.SchemaField("status", "STRING"),
    bigquery.SchemaField("project_ticket", "STRING"),
    bigquery.SchemaField("planned_dev_start", "TIMESTAMP"),
    bigquery.SchemaField("planned_dev_finish", "TIMESTAMP"),
    bigquery.SchemaField("planned_duration", "FLOAT"),
    bigquery.SchemaField("actual_start", "TIMESTAMP"),
    bigquery.SchemaField("actual_finish", "TIMESTAMP"),
    bigquery.SchemaField("actual_duration", "FLOAT"),
    bigquery.SchemaField("details_updated_at", "TIMESTAMP"),
    bigquery.SchemaField("last_updated_at", "TIMESTAMP"),
]

# Schema for temporary tables used in update operations
ISSUE_STATUS_UPDATE_SCHEMA = [
    bigquery.SchemaField("issue_key", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("summary", "STRING"),
    bigquery.SchemaField("status", "STRING"),
    bigquery.SchemaField("project_ticket", "STRING"),
    bigquery.SchemaField("planned_dev_start", "TIMESTAMP"),
    bigquery.SchemaField("planned_dev_finish", "TIMESTAMP"),
    bigquery.SchemaField("planned_duration", "FLOAT"),
    bigquery.SchemaField("last_updated_at", "TIMESTAMP"),
]

# Schema for temporary tables used in details update operations
ISSUE_DETAILS_UPDATE_SCHEMA = [
    bigquery.SchemaField("issue_key", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("actual_start", "TIMESTAMP"),
    bigquery.SchemaField("actual_finish", "TIMESTAMP"),
    bigquery.SchemaField("actual_duration", "FLOAT"),
    bigquery.SchemaField("details_updated_at", "TIMESTAMP"),
]


def get_schema_for_table(table_name):
    """
    Get the schema for a specific table.

    Args:
        table_name (str): The name of the table

    Returns:
        list: The schema for the table
    """
    schemas = {
        "jira_issues": JIRA_ISSUES_SCHEMA,
        "issue_status_update": ISSUE_STATUS_UPDATE_SCHEMA,
        "issue_details_update": ISSUE_DETAILS_UPDATE_SCHEMA,
    }

    return schemas.get(table_name, JIRA_ISSUES_SCHEMA)


def create_table_definition(table_id, schema=None):
    """
    Create a BigQuery table definition.

    Args:
        table_id (str): The ID of the table
        schema (list, optional): The schema for the table. Defaults to None.

    Returns:
        bigquery.Table: The table definition
    """
    if schema is None:
        schema = JIRA_ISSUES_SCHEMA

    return bigquery.Table(table_id, schema=schema)


def get_merge_query(target_table, source_table, operation_type="status_update"):
    """
    Get a MERGE query for updating BigQuery tables.

    Args:
        target_table (str): The target table to update
        source_table (str): The source table with new data
        operation_type (str): The type of operation ("status_update" or "details_update")

    Returns:
        str: The MERGE query
    """
    if operation_type == "status_update":
        return f"""
        MERGE `{target_table}` T
        USING `{source_table}` S
        ON T.issue_key = S.issue_key
        WHEN MATCHED THEN
          UPDATE SET 
            T.status = S.status,
            T.summary = S.summary,
            T.project_ticket = S.project_ticket,
            T.planned_dev_start = S.planned_dev_start,
            T.planned_dev_finish = S.planned_dev_finish,
            T.planned_duration = S.planned_duration,
            T.last_updated_at = S.last_updated_at
        WHEN NOT MATCHED THEN
          INSERT (issue_key, summary, status, project_ticket, planned_dev_start, planned_dev_finish, planned_duration, last_updated_at)
          VALUES (issue_key, summary, status, project_ticket, planned_dev_start, planned_dev_finish, planned_duration, last_updated_at)
        """
    elif operation_type == "details_update":
        return f"""
        MERGE `{target_table}` T
        USING `{source_table}` S
        ON T.issue_key = S.issue_key
        WHEN MATCHED THEN
          UPDATE SET 
            T.actual_start = S.actual_start,
            T.actual_finish = S.actual_finish,
            T.actual_duration = S.actual_duration,
            T.details_updated_at = S.details_updated_at
        """
    else:
        raise ValueError(f"Unknown operation type: {operation_type}")
