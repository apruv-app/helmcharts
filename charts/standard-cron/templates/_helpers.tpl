{{/*
Expand the name of the chart.
*/}}
{{- define "standard-cron.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "standard-cron.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "standard-cron.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "standard-cron.labels" -}}
helm.sh/chart: {{ include "standard-cron.chart" . }}
{{ include "standard-cron.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "standard-cron.selectorLabels" -}}
app.kubernetes.io/name: {{ include "standard-cron.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Resolve the pod's serviceAccountName.

Resolution order (first match wins):
  1. Top-level `serviceAccountName` (canonical string).
  2. Map-shaped `serviceAccount` with `create: true` — name is `serviceAccount.name`,
     defaulting to the chart fullname when unset. Pairs with the
     `serviceaccount.yaml` template, which renders a ServiceAccount resource
     in the same case.
  3. Map-shaped `serviceAccount` with `name` set but `create: false` — the user
     is referencing a SA created elsewhere.
  4. String-shaped `serviceAccount` (legacy; still accepted for back-compat).

Returns an empty string when none of the above matches, so the caller can
skip emitting the field via `with include`.
*/}}
{{- define "standard-cron.serviceAccountName" -}}
{{- if .Values.serviceAccountName -}}
{{- .Values.serviceAccountName -}}
{{- else if and (kindIs "map" .Values.serviceAccount) .Values.serviceAccount.create -}}
{{- default (include "standard-cron.fullname" .) .Values.serviceAccount.name -}}
{{- else if and (kindIs "map" .Values.serviceAccount) .Values.serviceAccount.name -}}
{{- .Values.serviceAccount.name -}}
{{- else if kindIs "string" .Values.serviceAccount -}}
{{- .Values.serviceAccount -}}
{{- end -}}
{{- end }}
