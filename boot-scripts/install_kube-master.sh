#!/bin/bash
######################################################################
#
# VARIABLES:
#   KUBE_VERSION = 1.0.6
#   KUBE_CLUSTER_IP_CIDR = 10.1.1.0/24
#   KUBE_ALLOW_PRIVILEGED = true
#   KUBE_API_LOG_FILE = /var/log/kube-apiserver.log
#   KUBE_CONTROLLER_MANAGER_LOG_FILE = /var/log/kube-controller-manager.log
#   KUBE_SCHEDULER_LOG_FILE = /var/log/kube-scheduler.log
#   KUBE_PROXY_LOG_FILE = /var/log/kube-proxy.log
#
# PORTS:
#     kube-apiserver = 8080, 6443 (TLS)
#######################################################################

## this stack extends the leader elect cluster, so lets source in the cluster profile and expose some variables to us
source /etc/profile.d/cluster

#etcd_version="${ETCD_VERSION:-2.2.0}"
#cluster_name="${CLUSTER_NAME:-kube-etcd}"
#dns_zone="${DNS_ZONE:-dev.aws.lcloud.com}"
#etcd_log_file="${ETCD_LOG_FILE:-/var/log/etcd.log}"

echo "installing kubernetes"

kube_dir="/opt/kubernetes"
(
    cd /tmp
    curl -L  "https://github.com/GoogleCloudPlatform/kubernetes/releases/download/v${KUBE_VERSION}/kubernetes.tar.gz" -o "kubernetes-latest.tar.gz"

    tar xzvf "kubernetes-latest.tar.gz"
    mv "kubernetes-latest.tar.gz" "$kube_dir"
    rm -f "kubernetes-latest.tar.gz"

    tar xzvf $kube_dir/kubernetes/server/kubernetes-server-linux-amd64.tar.gz
    mv $kube_dir/kubernetes $kube_dir/kubernetes-latest
    cp $kube_dir/kubernetes-latest/server/bin/* $kube_dir/
    rm -rf $kube_dir/kubernetes-latest
)

cd "$kube_dir"
name="$(echo $MY_IPADDRESS | perl -pe 's{\.}{}g')"

nohup ./kube-apiserver \
    --admission-control=NamespaceLifecycle,NamespaceExists,LimitRanger,SecurityContextDeny,ResourceQuota \
    --etcd_servers=http://${CLUSTER_NAME}.${DNS_ZONE}:2379  \
    --insecure-bind-address=0.0.0.0 \
    --service-cluster-ip-range=${KUBE_MASTER_SERVICE_IP_CIDRS} \
    --allow-privileged=${KUBE_ALLOW_PRIVILEGED} \
    --v=2 \
    2>&1 >> ${KUBE_API_LOG_FILE} &

nohup ./kube-controller-manager \
    --master=http://${KUBE_MASTER_NAME}.${DNS_ZONE}:8080 \
    --v=2 \
    2>&1 >> ${KUBE_CONTROLLER_MANAGER_LOG_FILE} &

nohup ./kube-scheduler \
    --master=http://${KUBE_MASTER_NAME}.${DNS_ZONE}:8080 \
    --address=${MY_IPADDRESS} \
    --v=2 \
    2>&1 >> ${KUBE_SCHEDULER_LOG_FILE} &

nohup ./kube-proxy \
    --master=http://${KUBE_MASTER_NAME}.${DNS_ZONE}:8080 \
    --v=2 \
    2>&1 >> ${KUBE_PROXY_LOG_FILE} &
