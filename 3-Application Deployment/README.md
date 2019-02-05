# Introduction

In this part we will explore the procedures of deploying an application. The very simple example comes from Kubernetes official tutorial, [click here to read](https://kubernetes.io/docs/tutorials/hello-minikube/#create-a-deployment).

## HelloWorld Application

In folder `HelloWorld Project`, there is the application's source code and its relevant Dockerfile.

First of all, we build our application Docker image and push it to the registry (like [DockerHub](https://hub.docker.com/)).

### Create a Deployment

A Kubernetes Pod is a group of one or more Containers, tied together for the purposes of administration and networking. The Pod in this tutorial has only one Container. A Kubernetes Deployment checks on the health of your Pod and restarts the Pod’s Container if it terminates. Deployments are the recommended way to manage the creation and scaling of Pods.

```
kubectl create deployment hello-k8s --image=gluckzhang/hello-k8s:v1
kubectl get deployments
```

The output should be something like the following:

```
NAME        READY   UP-TO-DATE   AVAILABLE   AGE
hello-k8s   1/1     1            1           17d
```

