#!/usr/bin/env python3

import sys
import argparse

from cloudbridge.factory import CloudProviderFactory
from cloudbridge.factory import ProviderList
from cloudbridge.interfaces.exceptions import DuplicateResourceException

def main(arguments):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('filepath', help="File to upload", type=str)
    parser.add_argument('destination', help="Destination in bucket", type=str)
    parser.add_argument('-b', '--bucket', help="Name of destination bucket", type=str)
    parser.add_argument('-p', '--provider',
                        choices=[ProviderList.__dict__[p] for p in ProviderList.__dict__.keys() if all(x not in p for x in ['_', 'MOCK'])],
                        help='Name of provider to use')
    parser.add_argument('-r', '--retries', help="Maximum number of retries. Default = 5", type=int, default=5)
    args = parser.parse_args(arguments)
    provider = CloudProviderFactory().create_provider(args.provider, {})
    try:
        bucket = provider.storage.buckets.create(args.bucket)
    except DuplicateResourceException:
        bucket = provider.storage.buckets.get(args.bucket)
    ob = bucket.objects.create(args.destination)
    uploaded = False
    count = 0
    while not uploaded:
        print(f'Trying for the {count}th time')
        uploaded = ob.upload_from_file(args.filepath)
        count += 1
    print(f'Uploaded: {args.filepath} to bucket {args.bucket} at location {args.destination}')

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))