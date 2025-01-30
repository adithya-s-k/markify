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

# Deployment Guide

## Prerequisites

- **azure-cli**
- **kubectl**
- **docker** (for local testing)

---

## AKS Cluster Setup

### 1. Login to Azure and Set Subscription

```bash
az login
az account set --subscription <your-subscription-id>
```
*(If network issues occur, login via web before running `az login`)*

### 2. Create AKS Cluster with GPU Nodes

```bash
az aks create     --resource-group <your_resource_name> \  # e.g., omniparse_kubecluster
    --name <kube_service_name> \  # e.g., markify
    --node-count 2     --enable-cluster-autoscaler     --min-count 1     --max-count 5     --node-vm-size Standard_NC4as_T4_v3     --generate-ssh-keys     --network-plugin azure
```

#### Add GPU Node Pool

```bash
az aks nodepool add     --resource-group <your_resource_name> \  # e.g., omniparse_kubecluster
    --cluster-name <kube_service_name> \  # e.g., markify
    --name gpunodepool     --node-count 1     --node-vm-size Standard_NC4as_T4_v3     --node-taints sku=gpu:NoSchedule     --labels sku=gpu
```

#### Get AKS Credentials

```bash
az aks get-credentials --resource-group <your_resource_name> --name <kube_service_name>
```

---

### 3. Create AKS Cluster with CPU Nodes

```bash
az aks create     --resource-group omniparse_kubecluster     --name markify     --node-count 2     --enable-cluster-autoscaler     --min-count 1     --max-count 5     --node-vm-size Standard_A2m_v2     --generate-ssh-keys     --network-plugin azure
```

#### Get AKS Credentials

```bash
az aks get-credentials --resource-group omniparse_kubecluster --name markify
```

---

## Apply Kubernetes Manifests

```bash
kubectl apply -k k8s/base
kubectl apply -k k8s/overlays/production
```

### 4. Get Cluster Resources

```bash
kubectl get all -n production
```

### 5. Get External IP for Indexify Service

```bash
kubectl get svc -n production indexify -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

### 6. Run API Tests

```bash
python3 tests/test_api.py
```

### 7. Monitor Pods

```bash
kubectl get pods -n production -w
```

---

## NVIDIA Plugin Deployment

To enable GPU support on AKS, deploy the NVIDIA plugin:

```bash
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.1/nvidia-device-plugin.yml --validate=false
```

---

## Deploy Application

### Development/Testing Environment

```bash
kubectl apply -k k8s/overlays/development
```

### Production Environment

```bash
kubectl apply -k k8s/overlays/production
```

---

### 8. Run API Tests (Production)

Replace `<EXTERNAL-IP>` with the actual IP:

```bash
python3 tests/test_api.py
```

---

## Scaling Test

To scale the service and test it, start the load test from multiple terminals:

#### In Terminal 1

```bash
python3 tests/test_api.py
```

#### In Terminal 2

```bash
kubectl get pods -n production -w
```

---

## Check All Components Are Running

For **Development**:

```bash
kubectl get all -n development
```

For **Production**:

```bash
kubectl get all -n production
```

---

## Sanity Checks

### 1. Cluster Health

#### Check Nodes

```bash
kubectl get nodes
kubectl describe nodes | grep -i gpu
```

#### Check Pods

For **Development**:

```bash
kubectl get pods -n development
kubectl describe pods -n development  # Check for any issues
```

For **Production**:

```bash
kubectl get pods -n production
kubectl describe pods -n production  # Check for any issues
```

#### Run API Tests

```bash
python3 -m pytest -s -v tests/test_api.py --log-cli-level=INFO --disable-warnings
```

#### Get Pod Start Times

```bash
kubectl get pods -n production -o jsonpath='{range .items[*]}{.metadata.name}{"	"}{.status.startTime}{"
"}{end}'
```

### 2. Check Services

For **Development**:

```bash
kubectl get svc -n indexify-dev
```

For **Production**:

```bash
kubectl get svc -n indexify-prod
```

#### View Logs

For **Development**:

```bash
kubectl logs -n development deployment/indexify
kubectl logs -n development deployment/pdf-parser
```

For **Production**:

```bash
kubectl logs -n production deployment/indexify
kubectl logs -n production deployment/pdf-parser
```

---

## Monitoring Usage

```bash
kubectl get pods -n development -o wide  # or production
kubectl describe nodes | grep -A8 "Allocated resources"
kubectl top pods -n development  # or production
kubectl top nodes
```

---

## Scaling

To scale deployments:

```bash
kubectl scale deployment pdf-parser -n development --replicas=2  # or production
kubectl scale deployment indexify -n development --replicas=3  # or production
```

---

## Teardown

To remove the deployment:

```bash
kubectl delete -k k8s/overlays/development
kubectl delete -k k8s/overlays/production
```

To delete the AKS cluster:

```bash
az aks delete --resource-group <your_resource_name> --name <kube_service_name>
```

---

![Terminal Screenshot](https://github.com/adithya-s-k/markify/blob/main/terminal.png?raw=true)
