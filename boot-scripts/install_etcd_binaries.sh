#!/bin/bash
######################################################################
#
# VARIABLES:
#   ETCD_PKG_VERSION = 2.2.0
#
#######################################################################

etcd_pkg_version="${ETCD_PKG_VERSION:-2.2.0}"
etcd_log_file="${ETCD_LOG_FILE:-/var/log/etcd.log}"
echo "installing etcd"

touch "$etcd_log_file"
etcd_dir="/opt/etcd"
(
    cd /tmp
    curl -L  "https://github.com/coreos/etcd/releases/download/v${etcd_pkg_version}/etcd-v${etcd_pkg_version}-linux-amd64.tar.gz" -o "etcd-v${etcd_pkg_version}-linux-amd64.tar.gz"

    tar xzvf "etcd-v${etcd_pkg_version}-linux-amd64.tar.gz"
    mv "etcd-v${etcd_pkg_version}-linux-amd64" "$etcd_dir"
)

