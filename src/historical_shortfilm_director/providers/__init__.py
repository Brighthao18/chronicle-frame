"""Optional provider-specific planning policies; adapters never invent integrations."""


def provider_qc(root, meta):
    if meta.get("generator") == "flow":
        from .flow.qc import flow_project_warnings

        return flow_project_warnings(root, meta)
    return []
