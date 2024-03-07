import os

def get_from_os():
    config = {
        "PROJECT_ID": os.environ.get("PROJECT_ID"),
        "LOCATION": os.environ.get("LOCATION", "us"),
        "PROCESSOR_ID": os.environ.get("PROCESSOR_ID"),
        "MIME_TYPE": os.environ.get("MIME_TYPE", "application/pdf"),
        "FIELD_MASK": os.environ.get("FIELD_MASK", "text,entities,pages.pageNumber"),
        "PROCESSOR_VERSION_ID": os.environ.get("PROCESSOR_VERSION_ID"),
        "GCS_OUTPUT_URI": os.environ.get("GCS_OUTPUT_URI"),
        "DATASET": os.environ.get("DATASET"),
        "TABLE": os.environ.get("TABLE")
    }

    return config