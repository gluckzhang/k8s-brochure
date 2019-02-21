# Introduction
[Jenkins](https://jenkins.io) is a self-contained, open source automation server which can be used to automate all sorts of tasks related to building, testing, and delivering or deploying software. It can be installed through native system packages, Docker, or even run standalone by any machine with a Java Runtime Environment (JRE) installed.

There is lots of benefit to run Jenkins in a Kubernetes cluster, for example:

- High availability: Jenkins does have a master-slave mode to improve availability. However traditionally, if the master node is broken, all the Jenkins service is down. With the help of Kubernetes, the master node (pod) is made self-healing.
- Dynamic scaling: When Jenkins is running a task, it creates a slave node (pod). After the job is done, the pod is cleaned up automatically. What's more, Kubernetes will smartly allocate the new pod to a free node. The computing resource is taken reasonably.

# Installation

## Preparation Steps

For a better management, we could create all the resources under a specific namespace like `kube-ops`.

```
kubectl create namespace kube-ops
```

Since Jenkins needs permanent storage when we use it for real, we need to create PV (Persistent Volume) and PVC (Persistent Volume Claim) first. ([Official introduction here](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)) In our OpenStack cluster, we have created another server out of the K8s cluster to provide NFS (Network File System) service. The OS is CentOS and the reference commands are as follows:

```
# install nfs add a specific user for it
yum -y install nfs-utils rpcbind
useradd -u nfs

# test if nfs service is successfully installed
rpcinfo -p localhost

# create the folder we want to share
mkdir -p /data/k8s-nfs
chmod a+w /data/k8s-nfs

# update the configuration
# because our k8s cluse and nfs server are in the same subnet, we restrict the access to 192.168.1.0/24
echo "/data/k8s-nfs 192.168.1.0/24(rw,async,no_root_squash)" >> /etc/exports
exportfs -r

# start relevant services
systemctl start rpcbind
systemctl start nfs-server

# start the services after system reboots
systemctl enable rpcbind
systemctl enable nfs-server

# test nfs service
showmount -e localhost
```

## Install Jenkins

- Use `jenkins-pvc.yaml` to create PV and PVC for Jenkins

```
kubectl create -f jenkins-pvc.yaml
```

- Use `jenkins-development.yaml` to create relevant deployment and service

```
kubectl create -f jenkins-development.yaml
```

- Use `jenkins-rbac.yaml` to create a service account and bind roles for it

```
kubectl create -f jenkins-rbac.yaml
```

- Finally, we could also create an ingress for Jenkins, so that we could directly visit it by hostname

```
kubectl create -f jenkins-ingress.yaml
```