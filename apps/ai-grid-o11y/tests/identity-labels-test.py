#!/usr/bin/env python3
"""Check that Loki retains the full identity dimensions as stream labels."""

import os
import subprocess

import yaml


ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
CHART = os.path.join(ROOT, "charts", "ai-grid-o11y")


def main():
    render = subprocess.run(
        ["helm", "template", "ai-grid-o11y", CHART],
        check=True, capture_output=True, text=True,
    ).stdout

    resource = None
    for document in yaml.safe_load_all(render):
        if document and document.get("kind") == "LokiStack":
            assert resource is None, "more than one LokiStack rendered"
            resource = document
    assert resource is not None, "no LokiStack rendered"

    assert resource["apiVersion"] == "loki.grafana.com/v1"
    assert resource["metadata"]["name"] == "usage-logs"

    limits = resource["spec"]["limits"]
    stream_labels = limits["global"]["otlp"]["streamLabels"]["resourceAttributes"]
    labels = {attribute["name"] for attribute in stream_labels}
    expected = {
        "service.name",
        "subscription",
        "organization_id",
        "user_id",
        "model",
        "response_type",
        "kubernetes_namespace_name",
        "cluster_name",
        "cluster_id",
    }
    assert labels == expected, labels
    assert "identity_source" not in labels
    assert "identity_issuer" not in labels
    assert limits["global"]["retention"]["days"] == 30

    print("identity stream label checks: ok")


if __name__ == "__main__":
    main()
