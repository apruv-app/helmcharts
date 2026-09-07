# Optional probes and pod labels (0.1.9)

`livenessProbe`, `readinessProbe`, and `startupProbe` accept Kubernetes probe
objects for the primary service container. All default to empty maps, so services
without probe configuration retain the previous behavior. Existing configurations
that already contain these previously ignored values will activate them when
upgrading to 0.1.9; review paths, ports and timings before upgrading.

`podLabels` adds pod-template labels without changing Deployment selectors.
Selector label keys are reserved: attempting to override them fails rendering.
Sidecars configured through `extraContainers` keep their own probe configuration.

```yaml
podLabels:
  app.kubernetes.io/part-of: vendor-mocks
livenessProbe:
  httpGet:
    path: /health
    port: 8007
  periodSeconds: 10
readinessProbe:
  httpGet:
    path: /ready
    port: 8007
  timeoutSeconds: 6
startupProbe:
  httpGet:
    path: /health
    port: 8007
  periodSeconds: 2
  failureThreshold: 30
```

Probe objects are rendered as supplied; `healthCheckTimeoutSeconds` does not inject
probe defaults. Set `timeoutSeconds` in each probe when needed.

Merge triggers the existing chart packaging workflow. Consumers must explicitly
upgrade their pinned chart version; this PR does not change service deployments.
