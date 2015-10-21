kubernetes-master-cluster
=========================

This repository is the [CloudCoreo](https://www.cloudcoreo.com) stack for kubernetes master.

## Description
This stack will add a scalable, highly availabe, self healing kubernetes master cluster environment based on the [CloudCoreo leader election cluster here](http://hub.cloudcoreo.com/stack/leader-elect-cluster_35519).

Kubernetes allows you to manage a cluster of Linux containers as a single system to accelerate Dev and simplify Ops. The architecture is such that master and node clusters are both required. This is only the cluster for the master. This cluster expects an etcd cluster as well. If you need an etcd cluster there is one available [on the hub, here.](http://hub.cloudcoreo.com/stack/etcd-cluster_06252)

Interestingly there is no leader election with the kubernetes master. The requests are load balanced and the cluster exists simply for high availability. The durability is maintained by etcd.

Default values will result in a 2 datacenter deployment behind an internal load balancer addressable via a DNS record. 
## REQUIRED VARIABLES

### `DNS_ZONE`:
  * description: the dns zone (eg. example.com)
### ETCD_DNS_ZONE:
  * description: the zone in which the internal elb dns entry should be maintained

### `VPC_NAME`:
  * description: the cloudcoreo defined vpc to add this cluster to

### `VPC_CIDR`:
  * description: the cloudcoreo defined vpc to add this cluster to

### `PRIVATE_SUBNET_NAME`:
  * description: the private subnet in which the cluster should be added

### `PRIVATE_ROUTE_NAME`:
  * description: the private subnet in which the cluster should be added

### `KUBE_MASTER_KEY`:
  * description: the ssh key to associate with the instance(s) - blank will disable ssh

## OVERRIDE OPTIONAL VARIABLES

### `KUBE_VERSION`:
  * description: kubernetes version
  * default: 1.0.6

### `KUBE_MASTER_SERVICE_IP_CIDRS`:
  * default: 10.1.1.0/24
  * description: kubernetes service cidrs

### `KUBE_ALLOW_PRIVILEGED`:
  * default: true
  * description: allow privileged containers

### `KUBE_API_LOG_FILE`:
  * description: ha-nat log file
  * default: /var/log/kube-apiserver.log

### `KUBE_CONTROLLER_MANAGER_LOG_FILE`:
  * description: ha-nat log file
  * default: /var/log/kube-controller-manager.log

### `KUBE_SCHEDULER_LOG_FILE`:
  * description: ha-nat log file
  * default: /var/log/kube-scheduler.log

### `KUBE_PROXY_LOG_FILE`:
  * description: ha-nat log file
  * default: /var/log/kube-api.log

### `KUBE_MASTER_NAME`:
  * default: kube-master
  * description: the name of the cluster - this will become your dns record too

### `ETCD_CLUSTER_NAME`:
  * default: dev-etcd
  * description: the dns record of the etcd cluster

### `KUBE_MASTER_ELB_TRAFFIC_PORTS`:
  * default: 8080
  * description: ports that need to allow traffic into the ELB

### `KUBE_MASTER_ELB_TRAFFIC_CIDRS`:
  * default:10.0.0.0/8
  * description: the cidrs to allow traffic from on the ELB itself

### `KUBE_MASTER_TCP_HEALTH_CHECK_PORT`:
  * default: 10251
  * description: a tcp port the ELB will check every so often - this defines health and ASG termination

### `KUBE_MASTER_INSTANCE_TRAFFIC_PORTS`:
  * default: 1..65535
  * description: ports to allow traffic on directly to the instances

### `KUBE_MASTER_INSTANCE_TRAFFIC_CIDRS`:
  * default: 10.0.0.0/8
  * description: cidrs that are allowed to access the instances directly

### `KUBE_MASTER_SIZE`:
  * default: t2.small
  * description: the image size to launch

### `KUBE_MASTER_GROUP_SIZE_MIN`:
  * default: 2
  * description: the minimum number of instances to launch

### `KUBE_MASTER_GROUP_SIZE_MAX`:
  * default: 2
  * description: the maxmium number of instances to launch

### `KUBE_MASTER_HEALTH_CHECK_GRACE_PERIOD`:
  * default: 600
  * description: the time in seconds to allow for instance to boot before checking health

### `KUBE_MASTER_UPGRADE_COOLDOWN`:
  * default: 300
  * description: the time in seconds between rolling instances during an upgrade

### `TIMEZONE`:
  * default: America/LosAngeles
  * description: the timezone the servers should come up in

### `KUBE_MASTER_ELB_LISTENERS`:
  * default: [{ :elb_protocol => 'tcp', :elb_port => 8080, :to_protocol => 'tcp', :to_port => 8080 }]
  * description: The listeners to apply to the ELB

### `DATADOG_KEY`:
  * default: ''
  * description: "If you have a datadog key, enter it here and we will install the agent"

### `WAIT_FOR_KUBE_MASTER_MIN`:
  * default: true
  * description: true if the cluster should wait for all instances to be in a running state


## Tags
1. Container Management
1. Google
1. Kubernetes
1. High Availability
1. Master
1. Cluster

## Diagram
![alt text](https://raw.githubusercontent.com/lachie83/cloudcoreo-kubernetes-master-cluster/master/images/kubernetes-master-diagram.png "Kubernetes Master Cluster Diagram")

## Icon
![alt text](https://raw.githubusercontent.com/lachie83/cloudcoreo-kubernetes-master-cluster/master/images/kubernetes-master.png "kubernetes icon")

