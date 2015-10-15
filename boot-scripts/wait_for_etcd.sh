#!/bin/bash

cluster_name="${ETCD_CLUSTER_NAME}"
dns_zone="${ETCD_DNS_ZONE}"

(
    cd /opt/etcd
    while ./etcdctl --endpoint "http://${cluster_name}.${dns_zone}:2379" cluster-health 2>&1 | grep -q -e "exceeded header timeout" -e "failed to list members" -e "etcd cluster is unavailable or misconfigured"; do
	echo "waiting for etcd";
	sleep 5
    done
)

