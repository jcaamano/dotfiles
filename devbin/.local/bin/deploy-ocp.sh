#!/bin/bash

set -xe

if [ -z "$1" ]; then
    echo "Cluster install config not provided"
    exit 1
fi
INSTALL_CONFIG_TMPL=$1

IFS=. read tag platform ext <<<"${INSTALL_CONFIG_TMPL}"

if [ -z "$tag" ] || [ -z "$platform" ] || [ "$ext" != "install-config.yaml.tmpl" ]; then
    echo "Bad install config filename, use <tag>.[aws|gcp].install-config.yaml.tmpl>"
    exit 1
fi

if [ "$platform" != "gcp" ] && [ "$platform" != "aws" ]; then
    echo "Bad platform, use gcp or aws"
    exit 1
fi

declare -A DEFAULT_REGIONS
DEFAULT_REGIONS[aws]="us-east-1"
DEFAULT_REGIONS[gcp]="us-east1"

generated_cluster_name="jcaamano.${tag}.$(date +'%Y%m%d%H%M')"

CLUSTER_DIR="${CLUSTER_DIR:-/vagrant/work/clusters/${platform}/}"
INSTALL_CONFIG="${INSTALL_CONFIG:-${CLUSTER_DIR}/install-config.yaml}"

if [ -z "$OCP_VER" ] && [ -n "$OCP_CI_URL" ]; then
    CI_VER=$(curl -vs ${OCP_CI_URL} 2>&1 | grep "<a class=\"text-success\" href=\"/releasestream/4.15.0-0.ci/release/" -m1 | sed 's|.*>\([^<]\+\).*|\1|g')
    OCP_VER=$CI_VER
fi

if [ -n "${OCP_VER}" ]; then
    OCP_URL="${OCP_URL:-registry.ci.openshift.org/ocp/release:${OCP_VER}}"
fi

export CNI="${CNI:-OVNKubernetes}"
export CLUSTER_NAME="${CLUSTER_NAME:-${generated_cluster_name}}"
export WORKERS="${WORKERS:-3}"
export MASTERS="${MASTERS:-3}"
export REGION="${REGION:-${DEFAULT_REGIONS[$platform]}}"

if [ ! -f "${HOME}/.docker/config.json" ]; then
	echo "Missing ${HOME}/.docker/config.json"
	exit 1
fi
export PULL_SECRET=$(jq -r tostring ~/.docker/config.json)

if [ -f "${CLUSTER_DIR}/metadata.json" ]; then
    echo "Some cluster already deployed, exiting..."
    exit 1
fi

echo "Saving install config to ${INSTALL_CONFIG}"
envsubst < "${INSTALL_CONFIG_TMPL}" > "${INSTALL_CONFIG}"
cat "${INSTALL_CONFIG}"

OCP_INSTALL="openshift-install"
if [ -n "${OCP_URL}" ]; then
    echo "Using OCP ${OCP_URL}"
    oc adm release extract --command openshift-install "${OCP_URL}" --to "${CLUSTER_DIR}"
    OCP_INSTALL="${CLUSTER_DIR}/openshift-install"
fi

echo "Setting up the cluster ${CLUSTER_NAME} in ${CLUSTER_DIR}"
${OCP_INSTALL} create cluster --dir="${CLUSTER_DIR}"
