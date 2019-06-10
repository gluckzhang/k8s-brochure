# Tools for Kubernetes

This folder contains a series of tools which provide user-friendly interfaces to manage the Kubernetes cluster.

## Configfile Generator

The tool supports to easily manage Kubernetes config files such as:

- Generating config files for multiple user within different namespaces
- Generating config files for several users within already existed namespaces (so we won't need to create a new namespace)
- Deleting users if not needed anymore(Namespace itself need to be deleted manually since I don't want my script to accidentally deleting your entire namespace, so only the user will be removed)
- Merging config files for the same user to access to several different namespace in the same or different clusters
