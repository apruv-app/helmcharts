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


    def test_default_has_no_extra_volumes(self):
        pod = deployment({})['spec']['template']['spec']
        self.assertNotIn('volumes', pod)
        self.assertNotIn('volumeMounts', pod['containers'][0])

    def test_bounded_scratch_with_tls_and_application_security(self):
        for tls in [False, True]:
            with self.subTest(tls=tls):
                scratch = {'name': 'proof-scratch', 'emptyDir': {'medium': 'Memory', 'sizeLimit': '64Mi'}}
                mount = {'name': 'proof-scratch', 'mountPath': '/var/run/proof-media'}
                security = {'runAsUser': 65532, 'runAsNonRoot': True, 'readOnlyRootFilesystem': True,
                            'allowPrivilegeEscalation': False, 'capabilities': {'drop': ['ALL']}}
                pod = deployment({'tls': {'enabled': tls, 'secretName': 'existing-tls'},
                                  'extraVolumes': [scratch], 'extraVolumeMounts': [mount],
                                  'securityContext': security,
                                  'extraContainers': [{'name': 'proxy', 'image': 'proxy:test'}]})['spec']['template']['spec']
                app = next(c for c in pod['containers'] if c['name'] == 'standard-service')
                self.assertEqual(app['securityContext'], security)
                self.assertEqual(pod['volumes'], ([{'name': 'tls-certificate', 'secret': {'secretName': 'existing-tls'}}] if tls else []) + [scratch])
                self.assertEqual(app['volumeMounts'], ([{'name': 'tls-certificate', 'mountPath': '/etc/tls', 'readOnly': True}] if tls else []) + [mount])
                self.assertNotIn('volumeMounts', pod['containers'][0])


    def test_invalid_volume_references_and_collisions_fail_render(self):
        cases = [
            ({'extraVolumes': [{'name': 'scratch'}, {'name': 'scratch'}]}, 'duplicate volume name'),
            ({'tls': {'enabled': True}, 'extraVolumes': [{'name': 'tls-certificate'}]}, 'duplicate volume name'),
            ({'extraVolumeMounts': [{'name': 'missing', 'mountPath': '/scratch'}]}, 'unknown volume name'),
            ({'tls': {'enabled': True}, 'extraVolumeMounts': [{'name': 'tls-certificate', 'mountPath': '/etc/tls'}]}, 'duplicate mount path'),
        ]
        for values, error in cases:
            with self.subTest(error=error, values=values):
                result = render(values)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(error, result.stderr)
