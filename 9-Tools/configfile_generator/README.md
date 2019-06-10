# Introduction
This is a script with several functions for easily managing Kubernetes config files such as: 

* Generating config files for multiple user within different namespaces with a specified access role, 
	Either choose one of the role existed (admin,user,viewer) or provide a role yaml file 
* Generating config files for several users within already existed namespaces(so we won't need to create a new namespace) 
	Either choose one of the role existed (admin,user,viewer) or provide a role yaml file 
* Merging config files for the same user to access to several different namespace in the same or different clusters.
* Limit resource over N namespaces with a provided resource-quota.yaml file.


# Important to know before reading more

Q: How to set config files ?

A: In bash terminal (Note that you have to cd into the same folder as the config file)
The safest way is to replace directly your config file with the config file in $HOME/.kube/config with this new file(Do keep a copy of the old one first in this case)

There is also this other way with export KUBECONFIG="configfilename", but the variable rather being updated or expired too quickly so you will get an anonymous authentication error as if the configfilename has been unloaded.

Q: How to re-set the origin config files?

A:In bash terminal, Assumingly you have not move aroung you .kube folder or using a entirely different system than linux-based, the default path for your original config file should always be at $HOME/.kube/config
* export KUBECONFIG="$HOME/.kube/config"

Q: How to switch namespace or cluster, also know as switching context ?

A: In bash terminal 
* kubectl config get-contexts 

This will give you all available contexts for your config file to switch to. Note that only "those" contexts in your config file so if you want to access a cluster or a namespace not in your config file you have to acquire the config file containing that context(ask the guy who can give you the config file).

* kubectl config set-context contextname

contextname can be gotten from the previous command, check name column


# Dependencies
This requires the following to work. 

* Gcloud
* Kubectl
* A working K8s cluster
* ruamel.yaml API

## Install ruamel.yaml
[Link](https://yaml.readthedocs.io/en/latest/install.html) to doc. This tool is used for easily editing yaml file since almost everying things in K8s system can be output as a yaml file.

* pip install -U pip setuptools wheel
* pip install ruamel.yaml

# User manual

## IMPORTANT
When you use these command it will create the namespaces associated with the current cluster context. So if you have cluster1, cluster2, cluster3 and your namespace is on cluster1 then the functions will take the information from cluster1. So If you want to create a namespace on cluster2 you have to switch context to cluster2 first, then do these commands below.

### Access kinds:
* "admin" The person will be able to do anything within the namespace including securities creating new roles, allocating resource quotas, deleting the namespace itself which the admin is currently on(but not other namespace). 
* "user" Like admin the person can do anything within the namespace with restrictions that he can only view securities stuffs like roles, serviceaccount(to check who other than himself is on the same namespace), but not editing and deleting namespace. Same goes for resourcequotas he can only look at what has been specified. 
* "viewer": Can only view but not changing anything.

More details check the specified yaml file in forms folder for roles specifications. There is also a function where you can apply a custom role but you need to provide the role yaml file for that.

### CLI syntax
for instance creating a user with a specified access kind on a aldready existed namespace
* python ConstructAccess.py create --nsname namespace_name --akind access_kind user1 ... userN
this is the same as 
* python ConstructAccess.py create --akind access_kind --nsname namespace_name user1 ... userN
Meaning that we can interchange the flags and its argument with any other flag in any order you prefer, but user1 ... userN must still be at the end after the last flag argument.

All flags and their short-hands
* --nsname -a
* --uname -b
* --akind -c
* --rpath -d
* -rlpath -e

## Generating multiple config files for multiple namespaces with a particular accesskind within the namespaces

* python ConstructAccess.py create --akind access_kind namespace1 namespace2 ... namespaceN

This will create N config files for N different namespaces to be used. Also, the usernames created by this method is according to the format "namespaceN-user", so if your namespace is called tailp, then it will be "tailp-user" as username. 

After calling this method an access yaml with the format "access-NAMESPACENAME-NAMESPACE_USERNAME-accesskind.yaml"  will be created in a folder with name "NAMESPACENAME" for the sake of deletion for each namespaceN specified. For instance with

* python ConstructAccess.py create --akind admin myns1 myns2

This will create 2 folders, one named myns1 and the other myns2 . In myns1 an access file called "access-myns1-myns1-user-admin.yaml" will be created. The same logic goes for myns2.

If you want to remove the user using the created config file just go in the NAMESPACENAME folder created and find the yaml file for that user and use 
* kubectl delete -f accessfile.yaml

## Generating multiple users configs for an already existed namespace

* python ConstructAccess.py createEx --nsname namespace_name --akind accesskind username1  ... usernameN

This will create N config files for N different users within the already existed namespace_name with the specified accesskind. Note that each username should be unique and not the same as other already existed. 

You can check if your username is unique by looking up 
* kubectl get sa 

If any of your usernames match with one of these then you have to pick another one. Also you can check your namespace_name with

* kubectl get namespaces

This will list all the existed namespaces within your current cluster with your current-context privilege.
Also like the create method, this will also create an access yaml "access-NAMESPACENAME-NAMESPACE_USERNAME-accesskind.yaml" for each user specified in the folder named "namespace_name" for future deletion.

## Generating multiple namespaces with a custom access kind instead of the one specified

* python ConstructAccess.py createCustomRole --rpath role_file_path namespace1 namespace2 ... namepspaceN

This is like the normal create command with the difference that you have to provide a role.yaml file for your creating a custom privilege instead of using the access kinds(admin,user,viewer) like above. Example for a role.yaml file can be found in forms folder of this repo(role-admin.yaml for instance, or visit K8s page for more details)

Just like before with the create method, this will create a folder called "namespaceN" with an access file called "access-NAMESPACENAME-NAMESPACE_USERNAME-accesskind.yaml" .

## Generating multiple user configs for an already existed namespace with a custom access kind

* python ConstructAccess.py createExCustomeRole --nsname namespace_name --rpath role_file_path username1 username2 .... usernameN

Just like the createEx command instead of the standard access kinds specified here, you can use your own custom privilege by providing a role.yaml file and Also an access file will be created in the "namespace_name" folder.


## Merge config files

Let say that you want someone to access multiple different namespaces on the same or different clusters. This script also has that function where you can merge multiple files.

Note: Here I assume that you only want to generate the merged config file with the provided config files and not the one you are using right now. Otherwise you can just take the merged one and replace it with your current in $HOME/.kube/config (The default path of K8s config file) if you want to use the merged file.

Place all the config files you want to merge in this repo, also known as "K8sNamespaceRestrictedAccess" folder after cloning, then run

* python ConstructAccess.py merge configfile_1 configfile_2 .... configfile_N

It will generate a file called "mergedconfig" to use. Now the user can switching contexts and moving to different namespaces after setting the config file.

## Refetch config files

This is neccessary since the token for the service account will be expired after some time so, Kubernetes will automatically refresh this or maybe you lost the config file and want to re-aquire it. Therefore this also has a function which re-fetch the config file for you (with the updated token and other updated informations ofcourse). This will refetch N configfiles for N specified users.

* python ConstructAccess.py recreate namespace_name username1 username2 ... usernameN

namespace_name can be found with 
* kubectl get namespaces

username depends on which method you use. If it's the "create" method then it will be "namespace_name-user" otherwise if it's the "createEx" then in the right namespace the service account is in(you have to , it can be found with
* kubectl get sa

## Apply ResourcesQuota yaml over multiple namespace in one line

* python ConstructAccess limitRes --rlpath filepath namespace1 namespace2 ... namespaceN

Here "filepath" is the path of the yaml file for restricting resources in the mentioned namespaces. Check templates to have a look at "quota-mem-cpu.yaml" as an example of such file. 












