#!/usr/bin/env bash
# One-time setup to enable GitHub Actions OIDC -> AWS access for this repo.
# Run with credentials that can manage IAM (admin, or a scoped IAM-admin role).
# Re-running is safe: each step is idempotent or no-ops if already present.

set -euo pipefail

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
ROLE_NAME="cloudbridge-github-actions"
POLICY_NAME="cloudbridge-github-actions-policy"
REGION="us-east-1"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRUST_POLICY="${SCRIPT_DIR}/trust-policy.json"
PERMISSIONS_POLICY="${SCRIPT_DIR}/permissions-policy.json"

# 1. Register GitHub's OIDC provider in IAM (no-op if it already exists).
if ! aws iam get-open-id-connect-provider \
      --open-id-connect-provider-arn "arn:aws:iam::${ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com" \
      >/dev/null 2>&1; then
  aws iam create-open-id-connect-provider \
    --url "https://token.actions.githubusercontent.com" \
    --client-id-list "sts.amazonaws.com" \
    --thumbprint-list "ffffffffffffffffffffffffffffffffffffffff"
  # Thumbprint above is a placeholder — GitHub OIDC uses a JWKS endpoint and
  # AWS now validates the JWKS chain server-side, so the thumbprint is no
  # longer security-critical. Set any 40-char hex value.
fi

# 2. Render the trust policy with the real account id.
TRUST_RENDERED="$(mktemp)"
sed "s/ACCOUNT_ID/${ACCOUNT_ID}/g" "${TRUST_POLICY}" > "${TRUST_RENDERED}"

# 3. Create or update the role.
if aws iam get-role --role-name "${ROLE_NAME}" >/dev/null 2>&1; then
  aws iam update-assume-role-policy \
    --role-name "${ROLE_NAME}" \
    --policy-document "file://${TRUST_RENDERED}"
else
  aws iam create-role \
    --role-name "${ROLE_NAME}" \
    --assume-role-policy-document "file://${TRUST_RENDERED}" \
    --description "Assumed by GitHub Actions to run cloudbridge integration tests in ${REGION}"
fi

# 4. Attach an inline permissions policy (replaces on each run).
aws iam put-role-policy \
  --role-name "${ROLE_NAME}" \
  --policy-name "${POLICY_NAME}" \
  --policy-document "file://${PERMISSIONS_POLICY}"

ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

echo
echo "Role ready: ${ROLE_ARN}"
echo "Set this as a repo secret named AWS_OIDC_ROLE_ARN at:"
echo "  https://github.com/CloudVE/cloudbridge/settings/secrets/actions"
echo
echo "Then remove the AWS_ACCESS_KEY and AWS_SECRET_KEY repo secrets — they are no longer used."
