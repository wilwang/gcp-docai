# Document AI Workbench Summarizer Processor Example
This is an example workflow that is triggered when a user drops a PDF file into a Cloud Storage bucket. The Cloud Function will use Document AI Workbench summarizer processor to summarize the contents of the file and then store the output in a different storage bucket. Another function then takes that output file and stores the extracted text and the summary into a BigQuery table.

The advantage of using Document AI Workbench is that the processor takes care of a lot of the work around chunking when it comes to extracting large documents and passing context into the LLM models. All of the plumbing is taken care of for you when you use the workbench processors.

The code in this repository is for demonstration purposes only and is **NOT** intended for use directly in production environments.

## Document AI Workbench
Document AI Workbench allows users to quickly generate predictions with generative AI or build their own processors from scratch. This code example shows the functionality of the new **Summarizer Processor** which is powered by generative AI models. You can read more about [how Docmument AI is powered by generative AI](https://cloud.google.com/blog/products/ai-machine-learning/document-ai-workbench-custom-extractor-and-summarizer).

## Pre-requesites
1. Create the summarizer processor in Document AI workbench by following [these instructions](https://cloud.google.com/document-ai/docs/workbench/build-summarizer-processor)
1. Create an `upload` bucket and an `output` bucket for where you will be dropping files and storing the outputs. [[Reference]](https://cloud.google.com/storage/docs/creating-buckets)
1. Whether you intend to use the default Compute service account or create a specific service account, you need to make sure that the correct roles are assigned to the service account:
    - Eventarc Event Receiver
    - Cloud Run Invoker
    - Document AI API User
    - BigQuery Data Editor 
1. The service account will also need access to the Cloud storage buckets
    - Read access to bucket and object on the `upload` bucket
    - Write access to bucket and object on the `output` bucket

## Deploying the Cloud Functions
We will be deploying gen2 Cloud functions. Gen2 functions have some advantagges over gen1. Read more about the [differences](https://cloud.google.com/functions/docs/concepts/version-comparison). 

We will also use Eventarc events from Cloud storage to drive our workflow. [Eventarc](https://cloud.google.com/eventarc/docs) lets you asynchronously deliver events from Google services, SaaS, and your own apps using loosely coupled services that react to state changes.


>**Note**
> 
> Eventarc trigger locations must be in the same region as the bucket; if bucket is "US", trigger location must be "US" as well

[Deploy the function](https://cloud.google.com/sdk/gcloud/reference/functions/deploy) to handle the Doc AI processing

```bash
gcloud functions deploy on_upload \
--gen2 \
--region=us-central1 \
--runtime=python39 \
--source=. \
--entry-point=on_upload \
--env-vars-file=config.yaml \
--trigger-event-filters="bucket=ww-seegrid-docai-workbench-uploads" \
--trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
--trigger-location=us
```

[Deploy the function](https://cloud.google.com/sdk/gcloud/reference/functions/deploy) to handle the summarization output to store in BigQuery

```bash
gcloud functions deploy on_output \
--gen2 \
--region=us-central1 \
--runtime=python39 \
--source=. \
--entry-point=on_output \
--env-vars-file=config.yaml \
--trigger-event-filters="bucket=ww-seegrid-docai-workbench-output" \
--trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
--trigger-location=us
```