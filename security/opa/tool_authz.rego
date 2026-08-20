# OPA policy for tool authorization — the external policy engine consulted by
# app/tools/authz.py for sensitive tools. Deny by default.
package bfsi.tools

import rego.v1

default allow := false

# Staff with explicit roles may execute sensitive tools within their tenant.
allow if {
    input.tool.sensitive
    input.subject.tenant_id == input.resource.tenant_id
    input.subject.roles[_] in {"compliance_officer", "fraud_analyst", "institution_admin"}
    input.approved == true
}

# High-risk action matrix: freeze, reverse, disburse, write-off always need
# human approval + a valid approval ticket.
high_risk_tools := {"freeze_account", "reverse_transaction", "disburse_loan", "write_off_loan"}

allow if {
    input.tool.name in high_risk_tools
    input.approval.ticket_id != ""
    input.approval.resolver_role in {"compliance_officer", "fraud_analyst"}
}

# Reject cross-tenant access explicitly.
deny["cross_tenant"] if {
    input.subject.tenant_id != input.resource.tenant_id
}

# Reject when the tool is unknown to the platform.
deny["unknown_tool"] if {
    not input.tool.registered
}