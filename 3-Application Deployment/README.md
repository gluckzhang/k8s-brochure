# Introduction

In this part we will explore the procedures of deploying an application. The very simple example comes from Kubernetes official tutorial, [click here to read](https://kubernetes.io/docs/tutorials/hello-minikube/#create-a-deployment).

## HelloWorld Application

In folder `HelloWorld Project`, there is the application's source code and its relevant Dockerfile.

First of all, we build our application Docker image and push it to the registry (like [DockerHub](https://hub.docker.com/)).

### Create a deployment

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

*Note that hello-k8s:v1 doesn't display pod name and IP information. If you want to try the latest `server.js`, you should create the deployment with `hello-k8s-deployment.yaml`.*

### Create a service

By default, the Pod is only accessible by its internal IP address within the Kubernetes cluster. To make the `hello-k8s` container accessible from outside the Kubernetes virtual network, you have to expose the Pod as a Kubernetes Service.

```
kubectl expose deployment hello-k8s --port=8888
```

The type of this deployment is `ClusterIP` by default, after creating it you could use the file `hello-k8s-ingress.yaml` to create an ingress for the application.

### Scaling the deployment

```
kubectl scale deployment hello-k8s --replicas=1
```

### Updating or rolling back the deployment


For example, if we created hello-k8s with `v1` in the beginning, and now we plan to update the image to the latest.

```
kubectl set image deployment/hello-k8s hello-k8s=gluckzhang/hello-k8s:latest --record=true
```

If something is wrong, we could also roll back the version. Alternatively, you can rollback to a specific revision by specifying it with `--to-revision`.

```
kubectl rollout undo deployment hello-k8s
```

*Some other useful commands we might use*

To see the rollout status:
```
kubectl rollout status deployment hello-k8s
```

To check the revisions of this deployment:
```
kubectl rollout history deployment hello-k8s
```