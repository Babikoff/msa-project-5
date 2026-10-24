#!/bin/bash
set -e

minikube start --driver=docker

# docker build (context is Exporter/, dockerfile is ExporterJob/Dockerfile)
cd Exporter
docker build -t exporterjob:latest -f ExporterJob/Dockerfile .
cd ..

# minikube image load
minikube image load exporterjob:latest

# apply kubernetes manifests
kubectl apply -f k8s/

