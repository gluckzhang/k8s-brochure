# Introduction
If you are into Docker and Kubernetes, and have some IaaS resource at hand. Probably you could try to build a nice Kubernetes cluster by yourself instead of deploying the work to some cloud platform. In this way you learn more about the design of Kubernetes and also have the total control of your cluster on host machine level.

# Some Good Reading Materials

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kubernetes中文指南/云原生应用架构实践手册](https://jimmysong.io/kubernetes-handbook/)

<!--more-->

# Step 0: Create Instances You Need

- Create a security group and a key pair for the cluster
This security group guarantees that all your nodes in the subnet could communicate with each other. And we control external access for security reasons.

- Create a router and a network model
If your OpenStack cluster is quite a fresh one, maybe you need to configure the network first. All the nodes are configured in the same internal IPv4 network. Then a router connects this network to the internet.

- Create 4 instances, 1 for the kubernetes master and another 3 for the minions
I did all the following setup in a Centos 7 system.

# Step 1: Basic Installations in Each Node

Every node needs to:

- Install Docker ([Official Doc](https://docs.docker.com/install/linux/docker-ce/centos/))

```
$ sudo yum install -y yum-utils \
  device-mapper-persistent-data \
  lvm2

$ sudo yum-config-manager \
    --add-repo \
    https://download.docker.com/linux/centos/docker-ce.repo

$ sudo yum install docker-ce
$ sudo systemctl enable docker.service && systemctl start docker.service
```

- Install kubeadm ([Official Doc](https://kubernetes.io/docs/setup/independent/create-cluster-kubeadm/))

Kubeadm is an official tool which helps you bootstrap a minimum viable Kubernetes cluster that conforms to best practices. With kubeadm, your cluster should pass [Kubernetes Conformance tests](https://kubernetes.io/blog/2017/10/software-conformance-certification). Kubeadm also supports other cluster lifecycle functions, such as upgrades, downgrade, and managing [bootstrap tokens](https://kubernetes.io/docs/reference/access-authn-authz/bootstrap-tokens/).

```
cat <<EOF > /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://packages.cloud.google.com/yum/repos/kubernetes-el7-x86_64
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://packages.cloud.google.com/yum/doc/yum-key.gpg https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
exclude=kube*
EOF

# Set SELinux in permissive mode (effectively disabling it)
setenforce 0
sed -i 's/^SELINUX=enforcing$/SELINUX=permissive/' /etc/selinux/config

yum install -y kubelet kubeadm kubectl --disableexcludes=kubernetes

systemctl enable kubelet && systemctl start kubelet
```

Some users on RHEL/CentOS 7 have reported issues with traffic being routed incorrectly due to iptables being bypassed. You should ensure `net.bridge.bridge-nf-call-iptables` is set to 1 in your `sysctl` config, e.g.

```
cat <<EOF >  /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF
sysctl --system
```

After this, we could create a single master cluster with kubeadm now.

# Step 2: Initilize The Master And Add Nodes

The master is the machine where the control plane components run, including etcd (the cluster database) and the API server (which the kubectl CLI communicates with).

At first, we need to install a pod network add-on. I use Flannel in the cluster, so the command is:

```
kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/bc79dd1505b0c8681ece4de4c0d86c5cd2643275/Documentation/kube-flannel.yml
```

Then run the following commands to initilize the master.

```
kubeadm init --pod-network-cidr=10.244.0.0/16
```

To make kubectl work for your non-root user, run these commands, which are also part of the `kubeadm init` output:

```
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

Now we could add other nodes into our cluster. The nodes are where your workloads (containers and pods, etc) run. To add new nodes to your cluster do the following for each machine:

- SSH to the machine
- Become root (e.g. `sudo su -`)
- Run the command that was output by kubeadm init. For example:

```
kubeadm join --token <token> <master-ip>:<master-port> --discovery-token-ca-cert-hash sha256:<hash>
```

# Check The Cluster Status

Now we should have set up a Kubernetes cluster successfully. If we run `kubectl get componentstatuses` or `kubectl get nodes` in the master, we shoud get something like:

```
NAME                 STATUS    MESSAGE              ERROR
scheduler            Healthy   ok                   
controller-manager   Healthy   ok                   
etcd-0               Healthy   {"health": "true"}   

NAME             STATUS   ROLES    AGE   VERSION
kube-master      Ready    master   6d    v1.13.2
kube-minions-1   Ready    <none>   6d    v1.13.2
kube-minions-2   Ready    <none>   6d    v1.13.2
kube-minions-3   Ready    <none>   6d    v1.13.2
```
