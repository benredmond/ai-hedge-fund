#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEBSITE_DIR="${ROOT_DIR}/website"
PUBLIC_COHORTS_DIR="${WEBSITE_DIR}/public/data/cohorts"

COHORT_ID="cohort-0"
CONTEXT_PACK="${ROOT_DIR}/data/context_packs/26-1-16.json"
STRATEGIES_SRC="${ROOT_DIR}/data/cohorts/${COHORT_ID}/strategies.json"
STRATEGIES_DEST="${PUBLIC_COHORTS_DIR}/${COHORT_ID}/strategies.json"
CONTEXT_DEST="${PUBLIC_COHORTS_DIR}/${COHORT_ID}/context.json"

mkdir -p "${PUBLIC_COHORTS_DIR}"
rm -rf "${PUBLIC_COHORTS_DIR:?}/"*

mkdir -p "${PUBLIC_COHORTS_DIR}/${COHORT_ID}"
cp "${STRATEGIES_SRC}" "${STRATEGIES_DEST}"
cp "${CONTEXT_PACK}" "${CONTEXT_DEST}"

echo "Synced ${COHORT_ID} and context pack $(basename "${CONTEXT_PACK}") to website public data."
