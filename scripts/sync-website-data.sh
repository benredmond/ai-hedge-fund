#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEBSITE_DIR="${ROOT_DIR}/website"
PUBLIC_COHORTS_DIR="${WEBSITE_DIR}/public/data/cohorts"

COHORT_ID="cohort-0"
CONTEXT_SRC="${ROOT_DIR}/data/cohorts/${COHORT_ID}/context.json"
STRATEGIES_SRC="${ROOT_DIR}/data/cohorts/${COHORT_ID}/strategies.json"
STRATEGIES_DEST="${PUBLIC_COHORTS_DIR}/${COHORT_ID}/strategies.json"
CONTEXT_DEST="${PUBLIC_COHORTS_DIR}/${COHORT_ID}/context.json"

if [[ ! -f "${CONTEXT_SRC}" ]]; then
  echo "Missing context pack: ${CONTEXT_SRC}" >&2
  echo "Generate it and save to data/cohorts/${COHORT_ID}/context.json" >&2
  exit 1
fi

mkdir -p "${PUBLIC_COHORTS_DIR}"
rm -rf "${PUBLIC_COHORTS_DIR:?}/"*

mkdir -p "${PUBLIC_COHORTS_DIR}/${COHORT_ID}"
cp "${STRATEGIES_SRC}" "${STRATEGIES_DEST}"
cp "${CONTEXT_SRC}" "${CONTEXT_DEST}"

echo "Synced ${COHORT_ID} and context pack $(basename "${CONTEXT_SRC}") to website public data."
