from summarize import process_document
from config import get_from_os
from google.cloud import storage, documentai, bigquery
import functions_framework

# Cloud Function handler to take a file and summarize it using docai workbench summarizer
# (https://cloud.google.com/document-ai/docs/workbench/build-summarizer-processor)
@functions_framework.cloud_event
def on_upload(cloud_event):
    config = get_from_os()
    
    print(config)

    # Validate that the CloudEvent is a Cloud Storage event.
    if cloud_event["type"] != "google.cloud.storage.object.v1.finalized":
        print("Unexpected event type: {}".format(cloud_event["type"]))
        return

    # Get the Cloud Storage event data.
    data = cloud_event.data

    # Get the bucket and file name from the Cloud Storage event data.
    bucket_name = data["bucket"]
    file_name = data["name"]

    # Construct the input uri
    gcs_input_uri = "gs://{}/{}".format(bucket_name, file_name)

    # Process the file for summarization
    metadata = process_document(project_id=config["PROJECT_ID"], 
        location=config["LOCATION"], 
        processor_id=config["PROCESSOR_ID"], 
        mime_type=config["MIME_TYPE"], 
        field_mask=config["FIELD_MASK"], 
        processor_version_id=config["PROCESSOR_VERSION_ID"], 
        gcs_input_uri=gcs_input_uri, 
        gcs_output_uri=config["GCS_OUTPUT_URI"])

    print("on_upload finish")
    print(metadata)


# Cloud Function to take summarized output and save in BigQuery
@functions_framework.cloud_event
def on_output(cloud_event):
    config = get_from_os()
    
    # Validate that the CloudEvent is a Cloud Storage event.
    if cloud_event["type"] != "google.cloud.storage.object.v1.finalized":
        print("Unexpected event type: {}".format(cloud_event["type"]))
        return

    # Get the Cloud Storage event data.
    data = cloud_event.data

    # Get the bucket and file name from the Cloud Storage event data.
    bucket_name = data["bucket"]
    file_name = data["name"]

    # Construct the file uri
    file_uri = "gs://{}/{}".format(bucket_name, file_name)

    # Retrieve the file from the bucket
    storage_client = storage.Client()
    blob = storage_client.bucket(bucket_name).blob(file_name)

    # Download JSON File as bytes object and convert to Document Object
    print(f"Fetching {blob.name}")
    document = documentai.Document.from_json(
        blob.download_as_bytes(), ignore_unknown_fields=True)

    # For a full list of Document object attributes, please reference this page:
    # https://cloud.google.com/python/docs/reference/documentai/latest/google.cloud.documentai_v1.types.Document
    extracted_text = document.text
    summary = document.entities[0].normalized_value.text

    # Save extracted_text and summary to BigQuery
    save_to_bq(config["DATASET"], config["TABLE"], file_uri, extracted_text, summary)

# Function to insert data into a BQ table
def save_to_bq(dataset, table, file_uri, extracted_text, summary):
    print("Saving to BigQuery")
    client = bigquery.Client()

    table_id = f"{dataset}.{table}"

    data = [{"output_file_uri": file_uri,
        "extracted_text": extracted_text,
        "summary": summary}]

    errors = client.insert_rows_json(table_id, data)
    if errors == []:
        print("New rows have been added.")
    else:
        print("Encountered errors while inserting rows: {}".format(errors))
