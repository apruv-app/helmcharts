"""Render contract tests: python -m unittest discover -s tests (requires PyYAML)."""
from pathlib import Path
import subprocess
import tempfile
import unittest
import yaml

CHART = Path(__file__).resolve().parents[1] / 'charts/standard-service'


def render(values):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml') as file:
        yaml.safe_dump(values, file)
        file.flush()
        result = subprocess.run(['helm', 'template', 'test', str(CHART), '-f', file.name], text=True, capture_output=True)
    return result


def deployment(values):
    result = render(values)
    assert result.returncode == 0, result.stderr
    return next(doc for doc in yaml.safe_load_all(result.stdout) if doc and doc['kind'] == 'Deployment')


def service(values):
    result = render(values)
    assert result.returncode == 0, result.stderr
    return next(doc for doc in yaml.safe_load_all(result.stdout) if doc and doc['kind'] == 'Service')


class DeploymentContract(unittest.TestCase):
    def test_defaults_preserve_no_probes_and_selector_labels(self):
        dep = deployment({})
        pod = dep['spec']['template']
        self.assertEqual(pod['metadata']['labels'], dep['spec']['selector']['matchLabels'])
        container = pod['spec']['containers'][0]
        for probe in ['livenessProbe', 'readinessProbe', 'startupProbe']:
            self.assertNotIn(probe, container)

    def test_configured_probes_labels_and_sidecar(self):
        probes = {
            'livenessProbe': {'httpGet': {'path': '/health', 'port': 8007}, 'periodSeconds': 10},
            'readinessProbe': {'httpGet': {'path': '/ready', 'port': 8007}, 'timeoutSeconds': 6},
            'startupProbe': {'tcpSocket': {'port': 8007}, 'failureThreshold': 30},
        }
        dep = deployment({**probes, 'podLabels': {'app.kubernetes.io/part-of': 'vendor-mocks'},
                          'extraContainers': [{'name': 'proxy', 'image': 'proxy:test'}]})
        pod = dep['spec']['template']
        self.assertEqual(pod['metadata']['labels']['app.kubernetes.io/part-of'], 'vendor-mocks')
        self.assertNotIn('app.kubernetes.io/part-of', dep['spec']['selector']['matchLabels'])
        for key, value in dep['spec']['selector']['matchLabels'].items():
            self.assertEqual(pod['metadata']['labels'][key], value)
        container = next(c for c in pod['spec']['containers'] if c['name'] == 'standard-service')
        for key, value in probes.items():
            self.assertEqual(container[key], value)
        self.assertNotIn('readinessProbe', pod['spec']['containers'][0])

    def test_each_probe_independently_and_nulls(self):
        for key in ['livenessProbe', 'readinessProbe', 'startupProbe']:
            dep = deployment({key: {'exec': {'command': ['true']}}})
            container = dep['spec']['template']['spec']['containers'][0]
            self.assertEqual(container[key]['exec']['command'], ['true'])
        dep = deployment({'podLabels': None, 'readinessProbe': None})
        self.assertNotIn('readinessProbe', dep['spec']['template']['spec']['containers'][0])

    def test_reserved_selector_labels_rejected(self):
        for key in deployment({})['spec']['selector']['matchLabels']:
            result = render({'podLabels': {key: 'different'}})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('must not override selector label', result.stderr)

    def test_recreate_strategy_does_not_add_rolling_update(self):
        dep = deployment({'deploymentStrategy': {'type': 'Recreate'}})
        self.assertEqual(dep['spec']['strategy'], {'type': 'Recreate'})

    def test_scalar_http_and_https_keep_legacy_service_port(self):
        svc = service({'service': {'ports': {'http': 8020, 'https': 8443}}})
        ports = {entry['name']: entry for entry in svc['spec']['ports']}
        self.assertEqual(ports['http']['port'], 3001)
        self.assertEqual(ports['http']['targetPort'], 8020)
        self.assertEqual(ports['https']['port'], 3001)
        self.assertEqual(ports['https']['targetPort'], 8443)
