# PDF Document Extraction and Indexing

The example builds a pipeline that extracts text, tables and figures from a PDF Document. It embeds the text, table and images from the document and writes them into ChromaDB.
This example also provides an alternate approach, that is OSS friendly, using Docling for document parsing and ElasticSearch as the vector store.

The pipeline is hosted on a server endpoint in one of the containers. The endpoint can be called from any Python application.

## Start the Server Endpoint

```bash
docker compose up
```

## Deploy the Graph
The [Graph](workflow.py) has all the code which performs PDF Parsing, embedding and writing the VectorDB. We will deploy the Graph on the server to create an Endpoint for our workflow. 
Make sure to deploy the right graph before running the example.

```bash
pip install indexify
```

```bash
python workflow.py
```

This stage deploys the workflow on the server. At this point, you can also open the [UI](http://localhost:8900) to see the deployed Graph.

After this, you can call the endpoint with PDFs to make Indexify start parsing documents.

## Calling the Endpoint 

```python
from indexify import RemoteGraph

graph = RemoteGraph.by_name("Extract_pages_tables_images_pdf")
invocation_id = graph.run(block_until_done=True, url="")
```

## Outputs 
You can read the output of every function of the Graph. For example,

```python
chunks = graph.output(invocation_id, "chunk_text")
```

The ChromaDB tables are populated automatically by the [ChromaDBWriter](https://github.com/tensorlakeai/indexify/blob/main/examples/pdf_document_extraction/chromadb_writer.py) class.
The name of the databases used in the example are `text_embeddings` and `image_embeddings`. The database running inside the container at port `8000` is forwarded to the host for convenience. 

For ElasticSearch, the service in this example is set-up using `docker-compose.yaml`. `elastic_writer.py` relies on docker networking to connect to it
and index the generated vectors.

## Vector Search

Once the documents are processed, you can query ChromaDB for vector search. Here is some [same code for that](https://github.com/tensorlakeai/indexify/blob/main/examples/pdf_document_extraction/retreive.py)

For ElasticSearch `es_retrieve.py` has some sample python code to query the indexes.

## Customization

Copy the folder, modify the code as you like and simply upload the new Graph.

```bash
python workflow.py
```

## Using GPU

You have to make a couple of changes to use GPUs for PDF parsing.
1. Uncomment the lines in the `pdf-parser-executor` block which mention uncommenting them would enable GPUs.
2. Use the `gpu_image` in the `PDFParser`, `extract_chunks` and `extract_images` class/functions so that the workflow routes the PDFParser into the GPU enabled image.




---

# deployment

## Prerequisites

- azure-cli
- kubectl
- docker (local testing)

## AKS cluster

1. Login to Azure and set subscription:
```bash
az login
az account set --subscription <your-subscription-id> # or if net, then login on web before running az login, automatic then
```

2. AKS cluster with GPU :
```bash
az aks create \
    --resource-group <your_resource_name> \ # omniparse_kubecluster
    --name <kube_servive_name> \ # named it markify
    --node-count 2 \
    --enable-cluster-autoscaler \
    --min-count 1 \
    --max-count 5 \
    --node-vm-size Standard_NC4as_T4_v3 \
    --generate-ssh-keys \
    --network-plugin azure

az aks nodepool add \
    --resource-group <your_resource_name> \ # omniparse_kubecluster
    --cluster-name <kube_servive_name> \ # named it markify
    --name gpunodepool \
    --node-count 1 \
    --node-vm-size Standard_NC4as_T4_v3 \
    --node-taints sku=gpu:NoSchedule \
    --labels sku=gpu

az aks get-credentials --resource-group <your_resource_name> --name <kube_servive_name>
```

### 1. deploy nvidia plugin
```bash
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.1/nvidia-device-plugin.yml --validate=false
```

### 2. deploy application

for development/testing environment:
```bash
kubectl apply -k k8s/overlays/development
```

for production environment:
```bash
kubectl apply -k k8s/overlays/production
```


kubectl get svc -n production indexify -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
# Run tests (replace <EXTERNAL-IP> with actual IP)
python3 tests/test_api.py


Scaling Test:

Start load test from multiple terminals:

bash
Copy
# In terminal 1
python3 tests/test_api.py

# In terminal 2
kubectl get pods -n production -w



Check all components are running:
```bash
kubectl get all -n development 

# For production
kubectl get all -n production
```

## sanity checks

### 1. cluster health
```bash
# nodes check
kubectl get nodes
kubectl describe nodes | grep -i gpu

# pods cehck (same for production too)
kubectl get pods -n development  # or indexify-prod
kubectl describe pods -n development  # Check for any issues
```


python3 -m pytest -s -v tests/test_api.py \
  --log-cli-level=INFO \
  --disable-warnings

kubectl get pods -n production \
  -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.startTime}{"\n"}{end}'

### 2. check services
  ```bash
kubectl get svc -n indexify-dev

# logs(same for production too)
kubectl logs -n development deployment/indexify
kubectl logs -n development deployment/pdf-parser
```

### monitoring usage

```bash
kubectl get pods -n development -o wide # or production
kubectl describe nodes | grep -A8 "Allocated resources"

kubectl top pods -n development # or production
kubectl top nodes
```

### scaling
haven't tested yet! but shoudl work (kube commands)

```bash
kubectl scale deployment pdf-parser -n development --replicas=2 # or production

kubectl scale deployment indexify -n development --replicas=3 # or production
```

## teardown 

remove deployment:
```bash
kubectl delete -k k8s/overlays/development
kubectl delete -k k8s/overlays/production

az aks delete --resource-group <your_resource_name> --name <kube_servive_name>
```

![alt text](https://github.com/adithya-s-k/markify/blob/main/terminal.png?raw=true)
