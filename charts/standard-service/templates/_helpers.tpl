{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "standard-service.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "standard-service.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "standard-service.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "standard-service.labels" -}}
helm.sh/chart: {{ include "standard-service.chart" . }}
{{ include "standard-service.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- if not .Values.selectorLabels }}
app.kubernetes.io/name: {{ include "standard-service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "standard-service.selectorLabels" -}}
app.kubernetes.io/name: {{ include "standard-service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "standard-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "standard-service.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Environment hostname
*/}}
{{- define "ingressHostname" -}}
{{- if .Values.hostnameOverride }}
{{- .Values.hostnameOverride }}
{{- else if not .Values.env }}
{{- required ".Values.env must be defined" .Values.env }}
{{- else if (eq .Values.env "dev") }}
{{- "dev.apruv.io" }}
{{- else if (eq .Values.env "prod") }}
{{- "prod.apruv.io" }}
{{- else }}
{{- fail ".Values.env must be dev, prod" }}
{{- end }}
{{- end }}

{{/*
Environment tls cert name
*/}}
{{- define "tlsCertName" -}}
{{- if .Values.tlsCertNameOverride }}
{{- .Values.tlsCertNameOverride }}
{{- else if not .Values.env }}
{{- required ".Values.env must be defined" .Values.env }}
{{- else if (eq .Values.env "dev") }}
{{- "apruv-io-tls" }}
{{- else if (eq .Values.env "prod") }}
{{- "apruv-io-tls" }}
{{- else }}
{{- fail ".Values.env must be dev, prod" }}
{{- end }}
{{- end }}