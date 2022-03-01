# Introduction

Ingress, added in Kubernetes v1.1, exposes HTTP and HTTPS routes from outside the cluster to services within the cluster. Traffic routing is controlled by rules defined on the ingress resource.

```
    internet
        |
   [ Ingress ]
   --|-----|--
   [ Services ]
```
An ingress can be configured to give services externally-reachable URLs, load balance traffic, terminate SSL, and offer name based virtual hosting. An ingress controller is responsible for fulfilling the ingress, usually with a loadbalancer, though it may also configure your edge router or additional frontends to help handle the traffic.

Since we deploy the Kubernetes cluster in OpenStack, the LoadBalancer service type is not provided. We could use [NGINX Ingress Controller for Kubernetes](https://github.com/kubernetes/ingress-nginx) to achieve this.

# Installation

- Deploy a default-backend first

The default backend is a service which handles all URL paths and hosts the nginx controller doesn't understand (i.e., all the requests that are not mapped with an Ingress).

Basically a default backend exposes two URLs:

```
/healthz that returns 200
/ that returns 404
```

`default-backend.yaml` is an example of the default-backend service.

- Deploy NGINX Ingress Controller

```
$ kubectl apply -f installation-mandatory-v0.22.0.yaml
```
*Note that this file is slightly modified from the official version. We added an argument for the nginx-ingress-controller, to directly specify the name of the default backend service. When I tried the [official yaml file](https://raw.githubusercontent.com/kubernetes/ingress-nginx/master/deploy/mandatory.yaml), it failed to detect the default backend service.*

When we deploy NGINX Ingress Controller in our cluster, the pods also had issues of `Services "ingress-nginx" not found`, which is relevant to this [issue](https://github.com/kubernetes/ingress-nginx/issues/2599). We created a fake ingress-nginx service to solve it.

```
$ kubectl apply -f fake-ingress-nginx.svc.yaml
```

## Disable Default Backend's Request Handling on Direct Public IPs

More discussions can be found here: [Can't disable default backend or handle direct public IP Request #971](https://github.com/nginxinc/kubernetes-ingress/issues/971)

# Expose The Ingress Controller

Because we couldn't use LoadBalancer service type in our own cluster, we have to use a NodePort service to expose the ingress controller. Then you could use `http(s)://<your-domain-name>:<port-number>` to visit your specific services.

```
$ kubectl apply -f nginx-ingress-controller.svc.yaml
```

# Example: Ingress for Kubernetes Dashboard

```
$ kubectl apply -f dashboard.ingress.yaml
```
After this step, you should be able to visit your dashboard with `https://<your-domain-name>:30443`. Port number `30443` was given in our `nginx-ingress-controller.svn.yaml`.
