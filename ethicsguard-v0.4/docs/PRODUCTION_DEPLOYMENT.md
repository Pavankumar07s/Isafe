# EthicsGuard v0.4 -- Production Deployment Guide

This document describes how to deploy EthicsGuard in a production Kubernetes environment with mTLS, secrets management, autoscaling, monitoring, and disaster recovery.

---

## Table of Contents

1. [Kubernetes Deployment Overview](#1-kubernetes-deployment-overview)
2. [Helm Chart Structure](#2-helm-chart-structure)
3. [cert-manager and mTLS Setup](#3-cert-manager-and-mtls-setup)
4. [Secrets Management](#4-secrets-management)
5. [Resource Recommendations](#5-resource-recommendations)
6. [Horizontal Pod Autoscaling](#6-horizontal-pod-autoscaling)
7. [Monitoring Stack](#7-monitoring-stack)
8. [Backup and Disaster Recovery](#8-backup-and-disaster-recovery)
9. [Network Policies](#9-network-policies)

---

## 1. Kubernetes Deployment Overview

EthicsGuard consists of four services, each deployed as a separate Kubernetes Deployment with a corresponding Service and optionally an Ingress.

```
                           +-----------------+
                           |   Ingress       |
                           |  (TLS termination)|
                           +--------+--------+
                                    |
              +----------+----------+----------+-----------+
              |          |          |          |            |
        +-----v----+ +--v-------+ +v--------+ +v---------+
        | Guardrail| | RedTeam  | | Eval    | | Dashboard|
        | Service  | | Service  | | Service | | Service  |
        | :8000    | | :8001    | | :8002   | | :8501    |
        +-----+----+ +----+-----+ +----+----+ +----+-----+
              |            |           |            |
              +------+-----+-----+-----+-----+-----+
                     |           |           |
              +------v-----+ +--v-------+ +-v-----------+
              | SQLite PVC | | Eval PVC | | Audit PVC   |
              | (shared)   | | (results)| | (logs)      |
              +------------+ +----------+ +-------------+
```

### Namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ethicsguard
  labels:
    app.kubernetes.io/part-of: ethicsguard
    pod-security.kubernetes.io/enforce: restricted
```

### Deployment Pattern (Guardrail Service Example)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: guardrail-service
  namespace: ethicsguard
  labels:
    app: guardrail-service
    app.kubernetes.io/name: guardrail-service
    app.kubernetes.io/version: "0.4.0"
    app.kubernetes.io/component: guardrail
    app.kubernetes.io/part-of: ethicsguard
spec:
  replicas: 2
  selector:
    matchLabels:
      app: guardrail-service
  template:
    metadata:
      labels:
        app: guardrail-service
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: ethicsguard-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
        - name: guardrail-service
          image: ethicsguard/guardrail-service:0.4.0
          ports:
            - containerPort: 8000
              protocol: TCP
          envFrom:
            - secretRef:
                name: ethicsguard-secrets
            - configMapRef:
                name: ethicsguard-config
          resources:
            requests:
              cpu: 250m
              memory: 512Mi
            limits:
              cpu: "1"
              memory: 1Gi
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 10
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
            failureThreshold: 3
          startupProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
            failureThreshold: 10
          volumeMounts:
            - name: sqlite-data
              mountPath: /data
            - name: audit-logs
              mountPath: /app/logs
            - name: tls-certs
              mountPath: /etc/tls
              readOnly: true
      volumes:
        - name: sqlite-data
          persistentVolumeClaim:
            claimName: ethicsguard-sqlite-pvc
        - name: audit-logs
          persistentVolumeClaim:
            claimName: ethicsguard-audit-pvc
        - name: tls-certs
          secret:
            secretName: ethicsguard-tls
```

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: guardrail-service
  namespace: ethicsguard
spec:
  selector:
    app: guardrail-service
  ports:
    - port: 8000
      targetPort: 8000
      protocol: TCP
  type: ClusterIP
```

---

## 2. Helm Chart Structure

The recommended Helm chart structure for EthicsGuard:

```
ethicsguard-helm/
  Chart.yaml
  values.yaml
  values-staging.yaml
  values-production.yaml
  templates/
    _helpers.tpl
    namespace.yaml
    configmap.yaml
    secrets.yaml                 # SealedSecret or ExternalSecret
    pvc.yaml
    guardrail-deployment.yaml
    guardrail-service.yaml
    guardrail-hpa.yaml
    redteam-deployment.yaml
    redteam-service.yaml
    redteam-hpa.yaml
    evaluation-deployment.yaml
    evaluation-service.yaml
    dashboard-deployment.yaml
    dashboard-service.yaml
    ingress.yaml
    networkpolicy.yaml
    servicemonitor.yaml          # For Prometheus Operator
    certificate.yaml             # For cert-manager
  tests/
    test-connection.yaml
```

### Key values.yaml Parameters

```yaml
# values.yaml
global:
  namespace: ethicsguard
  image:
    registry: ghcr.io/your-org
    tag: "0.4.0"
    pullPolicy: IfNotPresent

guardrailService:
  replicas: 2
  port: 8000
  resources:
    requests:
      cpu: 250m
      memory: 512Mi
    limits:
      cpu: "1"
      memory: 1Gi
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10
    targetCPUUtilization: 70

redteamService:
  replicas: 1
  port: 8001
  resources:
    requests:
      cpu: 250m
      memory: 512Mi
    limits:
      cpu: "1"
      memory: 1Gi

evaluationService:
  replicas: 1
  port: 8002
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: "2"
      memory: 2Gi

dashboardService:
  replicas: 1
  port: 8501
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 500m
      memory: 512Mi

ingress:
  enabled: true
  className: nginx
  tls: true
  certManager: true

monitoring:
  enabled: true
  serviceMonitor: true
  grafanaDashboard: true

compliance:
  mode: STANDARD
  rateLimit: 120

persistence:
  sqlite:
    size: 10Gi
    storageClass: standard
  audit:
    size: 20Gi
    storageClass: standard
  evalResults:
    size: 5Gi
    storageClass: standard
```

---

## 3. cert-manager and mTLS Setup

### Prerequisites

Install cert-manager in your cluster:

```bash
# Step 1: Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.0/cert-manager.yaml

# Step 2: Verify installation
kubectl wait --for=condition=Available deployment --all -n cert-manager --timeout=120s
```

### Certificate Issuer

```yaml
# Self-signed CA for internal mTLS (production: use a real CA)
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: ethicsguard-ca-issuer
spec:
  selfSigned: {}
---
# Root CA certificate
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: ethicsguard-root-ca
  namespace: ethicsguard
spec:
  isCA: true
  commonName: ethicsguard-root-ca
  secretName: ethicsguard-root-ca-secret
  duration: 8760h   # 1 year
  renewBefore: 720h  # 30 days
  issuerRef:
    name: ethicsguard-ca-issuer
    kind: ClusterIssuer
---
# Issuer using the root CA
apiVersion: cert-manager.io/v1
kind: Issuer
metadata:
  name: ethicsguard-issuer
  namespace: ethicsguard
spec:
  ca:
    secretName: ethicsguard-root-ca-secret
```

### Service Certificates

```yaml
# Certificate for each service
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: guardrail-service-tls
  namespace: ethicsguard
spec:
  secretName: guardrail-service-tls
  duration: 2160h    # 90 days
  renewBefore: 360h  # 15 days
  commonName: guardrail-service
  dnsNames:
    - guardrail-service
    - guardrail-service.ethicsguard
    - guardrail-service.ethicsguard.svc
    - guardrail-service.ethicsguard.svc.cluster.local
  issuerRef:
    name: ethicsguard-issuer
    kind: Issuer
```

Repeat for `redteam-service`, `evaluation-service`, and `dashboard-service`.

### mTLS Verification Steps

```bash
# Step 1: Verify certificates are issued
kubectl get certificates -n ethicsguard

# Step 2: Verify secrets are created
kubectl get secrets -n ethicsguard | grep tls

# Step 3: Check certificate status
kubectl describe certificate guardrail-service-tls -n ethicsguard

# Step 4: Test mTLS connection (from within cluster)
kubectl run --rm -it --image=curlimages/curl test-mtls -n ethicsguard -- \
  curl --cacert /etc/tls/ca.crt \
       --cert /etc/tls/tls.crt \
       --key /etc/tls/tls.key \
       https://guardrail-service:8000/health
```

---

## 4. Secrets Management

### Kubernetes Secrets (Baseline)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: ethicsguard-secrets
  namespace: ethicsguard
type: Opaque
stringData:
  OPENAI_API_KEY: "sk-..."
  INTERNAL_API_SECRET: "your-internal-secret"
  HIPAA_ENCRYPTION_KEY: "your-hipaa-passphrase"
  AUDIT_DB_PATH: "/data/ethicsguard_audit.db"
```

### Sealed Secrets (Recommended for GitOps)

```bash
# Step 1: Install sealed-secrets controller
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm install sealed-secrets sealed-secrets/sealed-secrets -n kube-system

# Step 2: Create a regular secret YAML (do NOT commit this)
kubectl create secret generic ethicsguard-secrets \
  --namespace ethicsguard \
  --from-literal=OPENAI_API_KEY=sk-... \
  --from-literal=INTERNAL_API_SECRET=your-secret \
  --from-literal=HIPAA_ENCRYPTION_KEY=your-passphrase \
  --dry-run=client -o yaml > /tmp/ethicsguard-secrets.yaml

# Step 3: Seal it (output is safe to commit to Git)
kubeseal --format yaml < /tmp/ethicsguard-secrets.yaml > sealed-ethicsguard-secrets.yaml

# Step 4: Apply
kubectl apply -f sealed-ethicsguard-secrets.yaml

# Step 5: Clean up plaintext
rm /tmp/ethicsguard-secrets.yaml
```

### ConfigMap for Non-Sensitive Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ethicsguard-config
  namespace: ethicsguard
data:
  COMPLIANCE_MODE: "STANDARD"
  RATE_LIMIT_PER_MINUTE: "120"
  ENABLE_PROMETHEUS: "true"
  LOG_LEVEL: "info"
  GUARDRAIL_BASE_URL: "http://guardrail-service:8000"
```

---

## 5. Resource Recommendations

### Per-Service Resource Allocation

| Service | CPU Request | CPU Limit | Memory Request | Memory Limit | Rationale |
|---|---|---|---|---|---|
| **Guardrail Service** | 250m | 1000m | 512Mi | 1Gi | Primary API; handles concurrent safety evaluations with multiple detectors |
| **Red-Team Service** | 250m | 1000m | 512Mi | 1Gi | Attack generation is CPU-intensive; batch evaluation requires HTTP client pooling |
| **Evaluation Service** | 500m | 2000m | 1Gi | 2Gi | Background eval jobs are long-running and memory-intensive (PDF generation) |
| **Dashboard Service** | 100m | 500m | 256Mi | 512Mi | Streamlit is lightweight; mostly serves static assets and proxies API calls |

### Storage Recommendations

| Volume | Size | Access Mode | Rationale |
|---|---|---|---|
| SQLite data | 10Gi | ReadWriteOnce | Audit database; grows with traffic |
| Audit logs | 20Gi | ReadWriteOnce | Log files; higher retention in non-GDPR modes |
| Eval results | 5Gi | ReadWriteOnce | PDF reports and intermediate results |

### Production Sizing Guidelines

| Traffic Profile | Guardrail Replicas | Total CPU | Total Memory |
|---|---|---|---|
| **Low** (<100 req/min) | 2 | 2 cores | 4Gi |
| **Medium** (100-1000 req/min) | 4-6 | 6 cores | 8Gi |
| **High** (>1000 req/min) | 8-10 | 12 cores | 16Gi |

---

## 6. Horizontal Pod Autoscaling

### Guardrail Service HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: guardrail-service-hpa
  namespace: ethicsguard
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: guardrail-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Pods
          value: 2
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Pods
          value: 1
          periodSeconds: 120
```

### Red-Team Service HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: redteam-service-hpa
  namespace: ethicsguard
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: redteam-service
  minReplicas: 1
  maxReplicas: 5
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 75
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 600
```

### Autoscaling Notes

- The Guardrail Service is the most latency-sensitive and should scale aggressively (minReplicas: 2).
- The Red-Team and Evaluation Services handle batch workloads and can tolerate slower scale-up.
- The Dashboard Service is typically single-replica; scale only if serving many concurrent browser sessions.
- The scaleDown stabilization window (300s) prevents flapping during traffic spikes.

---

## 7. Monitoring Stack

### Prometheus

EthicsGuard exports Prometheus metrics from the Guardrail Service when `ENABLE_PROMETHEUS=true`.

#### ServiceMonitor (for Prometheus Operator)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: ethicsguard-monitor
  namespace: ethicsguard
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app.kubernetes.io/part-of: ethicsguard
  endpoints:
    - port: http
      path: /metrics
      interval: 15s
      scrapeTimeout: 10s
  namespaceSelector:
    matchNames:
      - ethicsguard
```

#### Key Metrics to Monitor

| Metric | Type | Description |
|---|---|---|
| `ethicsguard_requests_total` | Counter | Total requests to /protect |
| `ethicsguard_requests_blocked_total` | Counter | Total blocked requests |
| `ethicsguard_requests_flagged_total` | Counter | Total flagged requests |
| `ethicsguard_latency_seconds` | Histogram | End-to-end /protect latency |
| `ethicsguard_detector_score` | Gauge | Per-detector scores (toxicity, bias, hallucination) |
| `ethicsguard_owasp_tags_total` | Counter | OWASP tags triggered (by tag) |

### Grafana

#### Dashboard Configuration

Import a Grafana dashboard JSON or create panels for:

1. **Request Rate** -- `rate(ethicsguard_requests_total[5m])`
2. **Block Rate** -- `rate(ethicsguard_requests_blocked_total[5m]) / rate(ethicsguard_requests_total[5m])`
3. **Latency P50/P95/P99** -- `histogram_quantile(0.50, rate(ethicsguard_latency_seconds_bucket[5m]))`
4. **Detector Score Distributions** -- `ethicsguard_detector_score` by detector type
5. **OWASP Tag Frequency** -- `topk(10, sum by (tag) (rate(ethicsguard_owasp_tags_total[1h])))`
6. **Error Rate** -- requests returning ERROR status

#### Alerting Rules

```yaml
groups:
  - name: ethicsguard-alerts
    rules:
      - alert: HighBlockRate
        expr: rate(ethicsguard_requests_blocked_total[5m]) / rate(ethicsguard_requests_total[5m]) > 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "EthicsGuard block rate exceeds 50%"
          description: "More than half of requests are being blocked. Investigate potential false positive spike or coordinated attack."

      - alert: HighLatency
        expr: histogram_quantile(0.99, rate(ethicsguard_latency_seconds_bucket[5m])) > 1.0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "EthicsGuard P99 latency exceeds 1 second"
          description: "The 99th percentile latency is above 1 second. Check detector performance and downstream API health."

      - alert: ServiceDown
        expr: up{job="ethicsguard"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "EthicsGuard service is down"
          description: "Prometheus cannot reach the EthicsGuard target. Check pod health and network connectivity."

      - alert: AuditGap
        expr: increase(ethicsguard_requests_total[5m]) > 0 and increase(ethicsguard_audit_records_total[5m]) == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Audit logging gap detected"
          description: "Requests are being processed but no audit records are being written. This is an ASI09 (Audit Trail Evasion) risk."
```

---

## 8. Backup and Disaster Recovery

### Backup Strategy

| Component | Backup Method | Frequency | Retention |
|---|---|---|---|
| SQLite audit database | PVC snapshot or `sqlite3 .backup` via CronJob | Every 6 hours | 30 days |
| Evaluation reports (PDF) | PVC snapshot | Daily | 90 days |
| Configuration (Helm values) | Git repository | On every change | Indefinite |
| Sealed secrets | Git repository (encrypted) | On every change | Indefinite |

### SQLite Backup CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: ethicsguard-backup
  namespace: ethicsguard
spec:
  schedule: "0 */6 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: backup
              image: alpine:3.19
              command:
                - /bin/sh
                - -c
                - |
                  apk add --no-cache sqlite
                  TIMESTAMP=$(date +%Y%m%d_%H%M%S)
                  sqlite3 /data/ethicsguard_audit.db ".backup '/backups/audit_${TIMESTAMP}.db'"
                  # Prune backups older than 30 days
                  find /backups -name "audit_*.db" -mtime +30 -delete
              volumeMounts:
                - name: sqlite-data
                  mountPath: /data
                  readOnly: true
                - name: backups
                  mountPath: /backups
          restartPolicy: OnFailure
          volumes:
            - name: sqlite-data
              persistentVolumeClaim:
                claimName: ethicsguard-sqlite-pvc
            - name: backups
              persistentVolumeClaim:
                claimName: ethicsguard-backups-pvc
```

### Disaster Recovery Procedure

1. **Service failure (single pod)**: Kubernetes automatically restarts failed pods. The HPA ensures minimum replica count is maintained.
2. **Database corruption**: Restore from the most recent PVC snapshot or CronJob backup. Apply with `sqlite3 /data/ethicsguard_audit.db ".restore '/backups/audit_LATEST.db'"`.
3. **Cluster failure**: Redeploy from Git (Helm chart + sealed secrets). Restore PVC data from off-cluster backup storage (e.g., S3, GCS).
4. **Secret compromise**: Rotate the compromised secret, regenerate the SealedSecret, and redeploy. For HIPAA encryption keys, re-encrypt audit logs with the new key.

### Recovery Time Objectives

| Scenario | RTO | RPO |
|---|---|---|
| Single pod failure | < 1 minute | Zero (state in PVC) |
| Full deployment redeploy | < 10 minutes | Up to 6 hours (backup interval) |
| Cluster recreation | < 1 hour | Up to 6 hours (backup interval) |

---

## 9. Network Policies

### Default Deny

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: ethicsguard
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
```

### Allow Inter-Service Communication

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-ethicsguard-internal
  namespace: ethicsguard
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/part-of: ethicsguard
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app.kubernetes.io/part-of: ethicsguard
  egress:
    - to:
        - podSelector:
            matchLabels:
              app.kubernetes.io/part-of: ethicsguard
```

### Allow Ingress from Load Balancer

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-ingress-to-guardrail
  namespace: ethicsguard
spec:
  podSelector:
    matchLabels:
      app: guardrail-service
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: ingress-nginx
      ports:
        - port: 8000
          protocol: TCP
```

### Allow External API Calls (OpenAI)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-openai-egress
  namespace: ethicsguard
spec:
  podSelector:
    matchLabels:
      app: guardrail-service
  policyTypes:
    - Egress
  egress:
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
      ports:
        - port: 443
          protocol: TCP
```

### Allow DNS Resolution

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: ethicsguard
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/part-of: ethicsguard
  policyTypes:
    - Egress
  egress:
    - to:
        - namespaceSelector: {}
      ports:
        - port: 53
          protocol: UDP
        - port: 53
          protocol: TCP
```

---

*This document was last updated on 2026-03-30 and applies to EthicsGuard v0.4.*
