"""
BigQuery Client Module

This module provides functionality for interacting with Google BigQuery,
including creating datasets and tables, inserting data, and performing queries.
"""

import os
import datetime
from google.cloud import bigquery
from google.cloud.exceptions import NotFound


class BigQueryClient:
    """
    A client for interacting with Google BigQuery.

    This class provides methods for creating datasets and tables,
    inserting data, and performing queries.
    """

    def __init__(self, dataset_id="jira_data", table_id="jira_issues"):
        """
        Initialize the BigQuery client.

        Args:
            dataset_id (str): The ID of the dataset to use
            table_id (str): The ID of the table to use
        """
        self.client = bigquery.Client()
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.table_ref = f"{dataset_id}.{table_id}"

        # Define the schema for the jira_issues table
        self.schema = [
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

    def ensure_dataset_exists(self):
        """
        Ensure the dataset exists, creating it if necessary.

        Returns:
            bool: True if the dataset exists or was created successfully
        """
        try:
            self.client.get_dataset(self.dataset_id)
            return True
        except NotFound:
            # Create the dataset
            dataset = bigquery.Dataset(f"{self.client.project}.{self.dataset_id}")
            dataset.location = "US"  # Set the dataset location
            self.client.create_dataset(dataset)
            print(f"Created dataset {self.dataset_id}")
            return True
        except Exception as e:
            print(f"Error ensuring dataset exists: {e}")
            return False

    def ensure_table_exists(self):
        """
        Ensure the table exists, creating it if necessary.

        Returns:
            bool: True if the table exists or was created successfully
        """
        try:
            self.client.get_table(self.table_ref)
            return True
        except NotFound:
            # Create the table
            table = bigquery.Table(
                f"{self.client.project}.{self.table_ref}", schema=self.schema
            )
            self.client.create_table(table)
            print(f"Created table {self.table_ref}")
            return True
        except Exception as e:
            print(f"Error ensuring table exists: {e}")
            return False

    def ensure_bigquery_setup(self):
        """
        Ensure the BigQuery dataset and table exist.

        Returns:
            bool: True if the setup was successful
        """
        return self.ensure_dataset_exists() and self.ensure_table_exists()

    def update_issues_status(self, issues):
        """
        Update the status of issues in BigQuery.

        Args:
            issues (list): A list of dictionaries containing issue data

        Returns:
            dict: A dictionary with counts of updated and inserted records
        """
        if not issues:
            return {
                "updated_count": 0,
                "inserted_count": 0,
                "error_count": 0,
                "errors": [],
            }

        try:
            # Prepare data for BigQuery
            rows_to_insert = []
            current_timestamp = datetime.datetime.utcnow().isoformat()

            for issue in issues:
                row = {
                    "issue_key": issue["issue_key"],
                    "summary": issue["summary"],
                    "status": issue["status"],
                    "project_ticket": issue.get("project_ticket", ""),
                    "planned_dev_start": issue.get("planned_dev_start", None),
                    "planned_dev_finish": issue.get("planned_dev_finish", None),
                    "planned_duration": issue.get("planned_duration", None),
                    "last_updated_at": current_timestamp,
                }
                rows_to_insert.append(row)

            # Create a temporary table for the new data
            temp_table_id = f"{self.dataset_id}.temp_issues_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            job_config = bigquery.LoadJobConfig(
                schema=self.schema,
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            )

            # Load data into temporary table
            job = self.client.load_table_from_json(
                rows_to_insert, temp_table_id, job_config=job_config
            )
            job.result()  # Wait for the job to complete

            # Perform MERGE operation to update existing records and insert new ones
            merge_query = f"""
            MERGE `{self.table_ref}` T
            USING `{temp_table_id}` S
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

            merge_job = self.client.query(merge_query)
            merge_result = merge_job.result()

            # Clean up temporary table
            self.client.delete_table(temp_table_id)

            # Get counts of updated and inserted rows
            # Note: This is an approximation as BigQuery doesn't provide exact counts
            count_query = f"""
            SELECT
              COUNTIF(operation = 'UPDATE') as updated_count,
              COUNTIF(operation = 'INSERT') as inserted_count
            FROM `{self.client.project}.{self.dataset_id}.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
            WHERE job_id = '{merge_job.job_id}'
            """

            count_job = self.client.query(count_query)
            count_result = list(count_job.result())

            if count_result:
                updated_count = count_result[0].get("updated_count", 0)
                inserted_count = count_result[0].get("inserted_count", 0)
            else:
                # Fallback if we can't get exact counts
                updated_count = len(issues)
                inserted_count = 0

            return {
                "updated_count": updated_count,
                "inserted_count": inserted_count,
                "error_count": 0,
                "errors": [],
            }

        except Exception as e:
            return {
                "updated_count": 0,
                "inserted_count": 0,
                "error_count": 1,
                "errors": [str(e)],
            }

    def update_issue_details(self, issues):
        """
        Update the details of issues in BigQuery.

        Args:
            issues (list): A list of dictionaries containing issue data

        Returns:
            dict: A dictionary with counts of updated records
        """
        if not issues:
            return {
                "updated_count": 0,
                "inserted_count": 0,
                "error_count": 0,
                "errors": [],
            }

        try:
            # Create a temporary table for the updated data
            temp_table_id = f"{self.dataset_id}.temp_details_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            job_config = bigquery.LoadJobConfig(
                schema=[
                    bigquery.SchemaField("issue_key", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("actual_start", "TIMESTAMP"),
                    bigquery.SchemaField("actual_finish", "TIMESTAMP"),
                    bigquery.SchemaField("actual_duration", "FLOAT"),
                    bigquery.SchemaField("details_updated_at", "TIMESTAMP"),
                ],
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            )

            # Load data into temporary table
            job = self.client.load_table_from_json(
                issues, temp_table_id, job_config=job_config
            )
            job.result()  # Wait for the job to complete

            # Perform MERGE operation to update details
            merge_query = f"""
            MERGE `{self.table_ref}` T
            USING `{temp_table_id}` S
            ON T.issue_key = S.issue_key
            WHEN MATCHED THEN
              UPDATE SET 
                T.actual_start = S.actual_start,
                T.actual_finish = S.actual_finish,
                T.actual_duration = S.actual_duration,
                T.details_updated_at = S.details_updated_at
            """

            merge_job = self.client.query(merge_query)
            merge_job.result()

            # Clean up temporary table
            self.client.delete_table(temp_table_id)

            return {
                "updated_count": len(issues),
                "inserted_count": 0,
                "error_count": 0,
                "errors": [],
            }

        except Exception as e:
            return {
                "updated_count": 0,
                "inserted_count": 0,
                "error_count": 1,
                "errors": [str(e)],
            }

    def get_issues_by_status(self, status):
        """
        Get issues with a specific status from BigQuery.

        Args:
            status (str): The status to filter by

        Returns:
            list: A list of issue keys
        """
        query = f"""
        SELECT issue_key
        FROM `{self.table_ref}`
        WHERE status = @status
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("status", "STRING", status),
            ]
        )

        query_job = self.client.query(query, job_config=job_config)
        results = list(query_job.result())

        return [row.get("issue_key") for row in results]

    def get_issues_needing_details(self, statuses):
        """
        Get issues that need details updated from BigQuery.

        Args:
            statuses (list): A list of statuses to filter by

        Returns:
            list: A list of issue keys
        """
        status_params = ", ".join([f"@status{i}" for i in range(len(statuses))])
        query = f"""
        SELECT issue_key
        FROM `{self.table_ref}`
        WHERE status IN ({status_params})
        AND (actual_start IS NULL OR actual_finish IS NULL OR actual_duration IS NULL)
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(f"status{i}", "STRING", status)
                for i, status in enumerate(statuses)
            ]
        )

        query_job = self.client.query(query, job_config=job_config)
        results = list(query_job.result())

        return [row.get("issue_key") for row in results]
