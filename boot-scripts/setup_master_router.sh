#!/bin/bash
######################################################################
#
# VARIABLES:
#   ETCD_PKG_VERSION = 2.2.0
#
#######################################################################

pip install netaddr

cp ./lib/kubernetes-master-router.py /opt
chmod +x /opt/kubernetes-master-router.py

(
    cd /opt
    nohup ./kubernetes-master-router.py --log-file "${KUBE_MASTER_ROUTER_LOG:-/var/log/kube-master-router.log}" --monitor-interval "${KUBE_MASTER_ROUTER_INTERVAL:-15}" --master-cidr-block "${KUBE_MASTER_SERVICE_IP_CIDR}" &

)
exit 0
