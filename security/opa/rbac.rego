# Global RBAC policy. Enforced both in-app (app/core/security/rbac.py) and
# mirrored here for auditability. Deny by default.
package bfsi.rbac

default allow := false

# Platform roles
allow if {
    input.subject.roles[_] == "platform_admin"
}

# Institution roles
allow if {
    input.subject.roles[_] == "institution_admin"
    input.resource.scope == "institution"
    input.subject.tenant_id == input.resource.tenant_id
}

# Staff roles scoped to their tenant and function
allow if {
    input.subject.roles[_] == "compliance_officer"
    input.resource.scope == "compliance"
    input.subject.tenant_id == input.resource.tenant_id
}

allow if {
    input.subject.roles[_] == "fraud_analyst"
    input.resource.scope == "fraud"
    input.subject.tenant_id == input.resource.tenant_id
}

# Self-service customers: only their own resources.
allow if {
    input.subject.roles[_] == "customer"
    input.resource.scope in {"customer_self", "loan_self"}
    input.resource.owner_id == input.subject.user_id
}

# Data classification: high-sensitivity resources require staff + approval.
deny["high_sensitivity_requires_staff"] if {
    input.resource.sensitivity == "high"
    not input.subject.roles[_] in {"compliance_officer", "fraud_analyst", "institution_admin", "platform_admin"}
}