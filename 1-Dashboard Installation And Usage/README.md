# Introduction

Kubernetes Dashboard is a general purpose, web-based UI for Kubernetes clusters. It allows users to manage applications running in the cluster and troubleshoot them, as well as manage the cluster itself. [Click here to visit the official GitHub repo](https://github.com/kubernetes/dashboard)

# Recommended Installation

To access Dashboard directly (without kubectl proxy) valid certificates should be used to establish a secure HTTPS connection. In our cluster, we use a self-signed certificate which are generated in the following steps.

- Generate private key and certificate signing request

Choose a proper folder on the master host, for example `~/certs`.

```
$ openssl genrsa -des3 -passout pass:x -out dashboard.pass.key 2048
$ openssl rsa -passin pass:x -in dashboard.pass.key -out dashboard.key
$ rm dashboard.pass.key
$ openssl req -new -key dashboard.key -out dashboard.csr
...
Country Name (2 letter code) [AU]: SE
...
A challenge password []:
...

```

**Note that you should specify the correct host address (like dashboard.yourdomain.com) when you create the certificate. It will cause some errors when you setup an ingress for the dashboard later if you want to expose your dashboard by a url.**

- Generate SSL certificate

```
$ openssl x509 -req -sha256 -days 365 -in dashboard.csr -signkey dashboard.key -out dashboard.crt
```

- Create Kubernetes secret resource

```
$ kubectl create secret tls kubernetes-dashboard-certs --cert=certs/dashboard.crt --key=certs/dashboard.key -n kube-system
```
*change the path to .crt and .key respectively*

- Deploy Dashboard

```
kubectl apply -f kubernetes-dashboard-v1.10.1.yaml
```
*You could also deploy the latest version with a url announced in the [GitHub repo]((https://github.com/kubernetes/dashboard))*

# Access the Dashboard

## kubectl proxy

If you directly deploy the dashboard by using the provided yaml file. You could access Dashboard from your local workstation by creating a secure channel to your Kubernetes cluster. Run the following command:

```
$ kubectl proxy
```

## NodePort

You could also edit `kubernetes-dashboard` service to expose a port and access your Dashboard with `https://<master-ip>:<port_number>`.

```
$ kubectl -n kube-system edit service kubernetes-dashboard
```

Change `type: ClusterIP` to `type: NodePort` and save file.

## Ingress

Will be introduced in the upcoming part.