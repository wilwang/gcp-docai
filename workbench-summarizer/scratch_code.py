from typing import Optional
from google.api_core.client_options import ClientOptions
from google.cloud import documentai as docai  # type: ignore
from google.cloud import storage
import re
from summarize import process_document

PROJECT_ID = "<PROJECT_ID>"
LOCATION = "us"
PROCESSOR_ID = "<PROCESSOR_ID>"
MIME_TYPE = "application/pdf"
FIELD_MASK = "text,entities,pages.pageNumber"
PROCESSOR_VERSION_ID = None
GCS_INPUT_URI = "gs://<BUCKET_INPUT>/<PDF_FILE>"
GCS_OUTPUT_URI = "gs://<BUCKET_OUTPUT>/"


def process_document_test (
    project_id: str,
    location: str,
    processor_id: str,
    mime_type: str,
    gcs_input_uri: str,
    gcs_output_uri: str,
    field_mask: Optional[str] = None,
    processor_version_id: Optional[str] = None
) -> None:
    # You must set the `api_endpoint` if you use a location other than "us".
    opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")

    client = docai.DocumentProcessorServiceClient(client_options=opts)

    gcs_document = docai.GcsDocument(
        gcs_uri = gcs_input_uri, 
        mime_type = mime_type)

    gcs_documents = docai.GcsDocuments(
        documents = [gcs_document])

    input_config = docai.BatchDocumentsInputConfig(
        gcs_documents = gcs_documents)

    gcs_output_config = docai.DocumentOutputConfig.GcsOutputConfig(
        gcs_uri = gcs_output_uri,
        field_mask = field_mask)

    output_config = docai.DocumentOutputConfig(gcs_output_config = gcs_output_config)

    if processor_version_id:
        # The full resource name of the processor version, e.g.:
        # `projects/{project_id}/locations/{location}/processors/{processor_id}/processorVersions/{processor_version_id}`
        name = client.processor_version_path(
            project_id, location, processor_id, processor_version_id
        )
    else:
        # The full resource name of the processor, e.g.:
        # `projects/{project_id}/locations/{location}/processors/{processor_id}`
        name = client.processor_path(project_id, location, processor_id)

    # Configure the batch process request
    request = docai.BatchProcessRequest(
        name = name,
        input_documents = input_config,
        document_output_config = output_config,
    )

    # Make the batch process request
    operation = client.batch_process_documents(request)

    try:
        print("Waiting for operation to complete...")
        response = operation.result()
    except (RetryError, InternalServerError) as e:
        print(e.message)

    # Once the operation is complete,
    # get output document information from operation metadata
    metadata = docai.BatchProcessMetadata(operation.metadata)

    if metadata.state != docai.BatchProcessMetadata.State.SUCCEEDED:
        raise ValueError(f"Batch Process Failed: {metadata.state_message}")

    storage_client = storage.Client()

    print("Output files:")
    # One process per Input Document
    for process in list(metadata.individual_process_statuses):
        # output_gcs_destination format: gs://BUCKET/PREFIX/OPERATION_NUMBER/INPUT_FILE_NUMBER/
        # The Cloud Storage API requires the bucket name and URI prefix separately
        matches = re.match(r"gs://(.*?)/(.*)", process.output_gcs_destination)
        if not matches:
            print(
                "Could not parse output GCS destination:",
                process.output_gcs_destination,
            )
            continue

        output_bucket, output_prefix = matches.groups()

        # Get List of Document Objects from the Output Bucket
        output_blobs = storage_client.list_blobs(output_bucket, prefix=output_prefix)

        # Document AI may output multiple JSON files per source file
        for blob in output_blobs:
            # Document AI should only output JSON files to GCS
            if blob.content_type != "application/json":
                print(
                    f"Skipping non-supported file: {blob.name} - Mimetype: {blob.content_type}"
                )
                continue

            # Download JSON File as bytes object and convert to Document Object
            print(f"Fetching {blob.name}")
            document = docai.Document.from_json(
                blob.download_as_bytes(), ignore_unknown_fields=True
            )

            # For a full list of Document object attributes, please reference this page:
            # https://cloud.google.com/python/docs/reference/documentai/latest/google.cloud.documentai_v1.types.Document

            # Read the text recognition output from the processor
            print("The document contains the following text:")
            print(document.text)

            # Read the summary output from the processor
            print("The summarization:")
            print(document.normalizedValue.text)            




    '''
    # For more information: https://cloud.google.com/document-ai/docs/reference/rest/v1/ProcessOptions
    # Optional: Additional configurations for processing.
    process_options = documentai.ProcessOptions(
        # Process only specific pages
        individual_page_selector=documentai.ProcessOptions.IndividualPageSelector(
            pages=[1]
        )
    )

    # Configure the process request
    request = documentai.ProcessRequest(
        name=name,
        raw_document=raw_document,
        field_mask=field_mask,
        process_options=process_options,
    )

    result = client.process_document(request=request)

    # For a full list of `Document` object attributes, reference this page:
    # https://cloud.google.com/document-ai/docs/reference/rest/v1/Document
    document = result.document

    # Read the text recognition output from the processor
    print("The document contains the following text:")
    print(document.text)
    '''

process_document(
    PROJECT_ID,
    LOCATION,
    PROCESSOR_ID,
    MIME_TYPE,
    GCS_INPUT_URI,
    GCS_OUTPUT_URI,
    FIELD_MASK
)