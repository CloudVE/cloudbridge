"""
    Provider implementation based on the moto library (mock boto). This mock
    provider is useful for running tests against cloudbridge but should not
    be used in tandem with other providers, in particular the AWS provider.
    This is because instantiating this provider will result in all calls to
    boto being hijacked, which will cause AWS to malfunction.
    See notes below.
"""
from moto import mock_ec2
from moto import mock_route53
from moto import mock_s3

import responses

from ..aws import AWSCloudProvider
from ...interfaces.provider import TestMockHelperMixin


class MockAWSCloudProvider(AWSCloudProvider, TestMockHelperMixin):
    """
    Using this mock driver will result in all boto communications being
    hijacked. As a result, this mock driver and the AWS driver cannot be used
    at the same time. Do not instantiate the mock driver if you plan to use
    the AWS provider within the same python process. Alternatively, call
    provider.tearDownMock() to stop the hijacking.
    """
    PROVIDER_ID = 'mock'

    def __init__(self, config):
        self.setUpMock()
        super(MockAWSCloudProvider, self).__init__(config)

    def setUpMock(self):
        """
        Let Moto take over all socket communications
        """
        self.ec2mock = mock_ec2()
        self.ec2mock.start()
        self.s3mock = mock_s3()
        self.s3mock.start()
        self.route53mock = mock_route53()
        self.route53mock.start()
        responses.add(
            responses.GET,
            self.AWS_INSTANCE_DATA_DEFAULT_URL,
            body=u"""
[
  {
    "family": "General Purpose",
    "enhanced_networking": false,
    "vCPU": 1,
    "generation": "current",
    "ebs_iops": 0,
    "network_performance": "Low",
    "ebs_throughput": 0,
    "vpc": {
      "ips_per_eni": 2,
      "max_enis": 2
    },
    "arch": [
      "x86_64"
    ],
    "linux_virtualization_types": [
        "HVM"
    ],
    "pricing": {
        "us-east-1": {
            "linux": {
                "ondemand": "0.0058",
                "reserved": {
                    "yrTerm1Convertible.allUpfront": "0.003881",
                    "yrTerm1Convertible.noUpfront": "0.0041",
                    "yrTerm1Convertible.partialUpfront": "0.003941",
                    "yrTerm1Standard.allUpfront": "0.003311",
                    "yrTerm1Standard.noUpfront": "0.0036",
                    "yrTerm1Standard.partialUpfront": "0.003412",
                    "yrTerm3Convertible.allUpfront": "0.002626",
                    "yrTerm3Convertible.noUpfront": "0.0029",
                    "yrTerm3Convertible.partialUpfront": "0.002632",
                    "yrTerm3Standard.allUpfront": "0.002169",
                    "yrTerm3Standard.noUpfront": "0.0025",
                    "yrTerm3Standard.partialUpfront": "0.002342"
                }
            }
        }
    },
    "ebs_optimized": false,
    "storage": null,
    "max_bandwidth": 0,
    "instance_type": "t2.nano",
    "ECU": "variable",
    "memory": 0.5,
    "ebs_max_bandwidth": 0
  },
  {
    "family": "General Purpose",
    "enhanced_networking": false,
    "vCPU": 96,
    "generation": "current",
    "ebs_iops": 80000.0,
    "network_performance": "25 Gigabit",
    "ebs_throughput": 1750.0,
    "vpc": {
      "ips_per_eni": 50,
      "max_enis": 15
    },
    "arch": [
      "x86_64"
    ],
    "linux_virtualization_types": [
        "HVM"
    ],
    "ebs_optimized": false,
    "storage": null,
    "max_bandwidth": 0,
    "instance_type": "m5.24xlarge",
    "ECU": 345.0,
    "memory": 384.0,
    "ebs_max_bandwidth": 14000.0
  },
  {
    "family": "General Purpose",
    "enhanced_networking": false,
    "vCPU": 96,
    "generation": "current",
    "ebs_iops": 80000.0,
    "network_performance": "25 Gigabit",
    "ebs_throughput": 1750.0,
    "vpc": {
      "ips_per_eni": 50,
      "max_enis": 15
    },
    "arch": [
      "x86_64"
    ],
    "linux_virtualization_types": [
        "HVM"
    ],
    "ebs_optimized": false,
    "storage": null,
    "max_bandwidth": 0,
    "instance_type": "m5.24xlarge",
    "ECU": 345.0,
    "memory": 384.0,
    "ebs_max_bandwidth": 14000.0
  },
  {
    "family": "Memory optimized",
    "enhanced_networking": false,
    "vCPU": 96,
    "generation": "current",
    "ebs_iops": 80000.0,
    "network_performance": "25 Gigabit",
    "ebs_throughput": 1750.0,
    "vpc": {
      "ips_per_eni": 50,
      "max_enis": 15
    },
    "arch": [
      "x86_64"
    ],
    "linux_virtualization_types": [
        "HVM"
    ],
    "ebs_optimized": false,
    "storage": null,
    "max_bandwidth": 0,
    "instance_type": "r5.24xlarge",
    "ECU": 347.0,
    "memory": 768.0,
    "ebs_max_bandwidth": 14000.0
  },
  {
    "family": "Memory optimized",
    "enhanced_networking": false,
    "vCPU": 96,
    "generation": "current",
    "ebs_iops": 80000.0,
    "network_performance": "25 Gigabit",
    "ebs_throughput": 1750.0,
    "vpc": {
      "ips_per_eni": 50,
      "max_enis": 15
    },
    "arch": [
      "x86_64"
    ],
    "linux_virtualization_types": [
        "HVM"
    ],
    "ebs_optimized": false,
    "storage": null,
    "max_bandwidth": 0,
    "instance_type": "r5d.24xlarge",
    "ECU": 347.0,
    "memory": 768.0,
    "ebs_max_bandwidth": 14000.0
  }
]
""")

    def tearDownMock(self):
        """
        Stop Moto intercepting all socket communications
        """
        self.s3mock.stop()
        self.ec2mock.stop()
        self.route53mock.stop()
