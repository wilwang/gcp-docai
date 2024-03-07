from typing import Optional
from google.api_core.client_options import ClientOptions
from google.cloud import documentai as docai

def process_document (
    project_id: str,
    location: str,
    processor_id: str,
    mime_type: str,
    gcs_input_uri: str,
    gcs_output_uri: str,
    field_mask: Optional[str] = None,
    processor_version_id: Optional[str] = None
):
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

    output_config = docai.DocumentOutputConfig(
        gcs_output_config = gcs_output_config)

    if processor_version_id:
        # The full resource name of the processor version, e.g.:
        # `projects/{project_id}/locations/{location}/processors/{processor_id}/processorVersions/{processor_version_id}`
        name = client.processor_version_path(
            project_id, location, processor_id, processor_version_id)
    else:
        # The full resource name of the processor, e.g.:
        # `projects/{project_id}/locations/{location}/processors/{processor_id}`
        name = client.processor_path(
            project_id, location, processor_id)

    # Configure the batch process request
    request = docai.BatchProcessRequest(
        name = name,
        input_documents = input_config,
        document_output_config = output_config)

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

    return metadata

