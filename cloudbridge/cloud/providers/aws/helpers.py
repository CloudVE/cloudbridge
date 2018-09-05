"""A set of AWS-specific helper methods used by the framework."""
import logging as log

from boto3.resources.params import create_request_parameters

from botocore import xform_name
from botocore.exceptions import ClientError
from botocore.utils import merge_dicts

from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.base.resources import ServerPagedResultList


def trim_empty_params(params_dict):
    """
    Given a dict containing potentially null values, trims out
    all the null values. This is to please Boto, which throws
    a parameter validation exception for NoneType arguments.
    e.g. Given
        {
            'GroupName': 'abc',
            'Description': None,
            'VpcId': 'xyz',
        }
    returns:
        {
            'GroupName': 'abc',
            'VpcId': 'xyz'
        }
    """
    log.debug("Removing null values from %s", params_dict)
    return {k: v for k, v in params_dict.items() if v is not None}


def find_tag_value(tags, key):
    """
    Finds the value associated with a given key from a list of AWS tags.

    :type tags: list of ``dict``
    :param tags: The AWS tag list to search through

    :type key: ``str``
    :param key: Name of the tag to search for
    """
    log.info("Searching for %s in %s", key, tags)
    for tag in tags or []:
        if tag.get('Key') == key:
            log.info("Found %s, returning %s", key, tag.get('Value'))
            return tag.get('Value')
    return None


class BotoGenericService(object):
    """
    Generic implementation of a Boto3 AWS service. Uses Boto3
    resource, collection and paging support to implement
    basic cloudbridge methods.
    """
    def __init__(self, provider, cb_resource, boto_conn, boto_collection_name):
        """
        :type provider: :class:`AWSCloudProvider`
        :param provider: CloudBridge AWS provider to use

        :type cb_resource: :class:`CloudResource`
        :param cb_resource: CloudBridge Resource class to wrap results in

        :type boto_conn: :class:`Boto3.Resource`
        :param boto_conn: Boto top level service resource (e.g. EC2, S3)
                          connection.

        :type boto_collection_name: ``str``
        :param boto_collection_name: Boto collection name that corresponds
                                    to the CloudBridge resource (e.g. key_pair)
        """
        self.provider = provider
        self.cb_resource = cb_resource
        self.boto_conn = boto_conn
        self.boto_collection_model = self._infer_collection_model(
            boto_conn, boto_collection_name)
        # Perform an empty filter to convert to a ResourceCollection
        self.boto_collection = (getattr(self.boto_conn, boto_collection_name)
                                .filter())
        self.boto_resource = self._infer_boto_resource(
            boto_conn, self.boto_collection_model)

    def _infer_collection_model(self, conn, collection_name):
        log.debug("Retrieving boto model for collection: %s", collection_name)
        return next(col for col in conn.meta.resource_model.collections
                    if col.name == collection_name)

    def _infer_boto_resource(self, conn, collection_model):
        log.debug("Retrieving resource model for collection: %s",
                  collection_model.name)
        resource_model = next(
            sr for sr in conn.meta.resource_model.subresources
            if sr.resource.model.name == collection_model.resource.model.name)
        return getattr(self.boto_conn, resource_model.name)

    def get(self, resource_id):
        """
        Returns a single resource.

        :type resource_id: ``str``
        :param resource_id: ID of the boto resource to fetch
        """
        try:
            log.debug("Retrieving resource: %s with id: %s",
                      self.boto_collection_model.name, resource_id)
            obj = self.boto_resource(resource_id)
            obj.load()
            log.debug("Successfully Retrieved: %s", obj)
            return self.cb_resource(self.provider, obj)
        except ClientError as exc:
            error_code = exc.response['Error']['Code']
            if any(status in error_code for status in
                   ('NotFound', 'InvalidParameterValue', 'Malformed', '404')):
                log.debug("Object not found: %s", resource_id)
                return None
            else:
                raise exc

    def _get_list_operation(self):
        """
        This function discovers the list operation for a particular resource
        collection. For example, given the resource collection model for
        KeyPair, it returns the list operation for it, as describe_key_pairs.
        """
        return xform_name(self.boto_collection_model.request.operation)

    def _to_boto_resource(self, collection, params, page):
        """
        This function duplicates some of the logic of the pages() method in
        boto.resources.collection.ResourceCollection. It will convert a raw
        json response to the corresponding Boto resource. It's necessary
        because paginators() return json responses, and there's no direct way
        to convert a paginated json response to a Boto Resource.
        """
        # pylint:disable=protected-access
        return collection._handler(collection._parent, params, page)

    def _get_paginated_results(self, limit, marker, collection):
        """
        If a Boto Paginator is available, use it. The results
        are converted back into BotoResources by directly accessing
        protected members of ResourceCollection. This logic can be removed
        depending on issue: https://github.com/boto/boto3/issues/1268.
        """
        # pylint:disable=protected-access
        cleaned_params = collection._params.copy()
        cleaned_params.pop('limit', None)
        cleaned_params.pop('page_size', None)
        # pylint:disable=protected-access
        params = create_request_parameters(
            collection._parent, collection._model.request)
        merge_dicts(params, cleaned_params, append_lists=True)

        client = self.boto_conn.meta.client
        list_op = self._get_list_operation()
        paginator = client.get_paginator(list_op)
        PaginationConfig = {}
        if limit:
            PaginationConfig = {'MaxItems': limit, 'PageSize': limit}

        if marker:
            PaginationConfig.update({'StartingToken': marker})

        params.update({'PaginationConfig': PaginationConfig})
        args = trim_empty_params(params)
        pages = paginator.paginate(**args)
        # resume_token is not populated unless the iterator is used
        items = pages.build_full_result()

        boto_objs = self._to_boto_resource(collection, args, items)
        resume_token = pages.resume_token
        return (resume_token, boto_objs)

    def _make_query(self, collection, limit, marker):
        """
        Decide between server or client pagination,
        depending on the availability of a Boto Paginator.
        See issue: https://github.com/boto/boto3/issues/1268
        """
        client = self.boto_conn.meta.client
        list_op = self._get_list_operation()
        if client.can_paginate(list_op):
            log.debug("Supports server side pagination. Server will"
                      " limit and page results.")
            res_token, items = self._get_paginated_results(limit, marker,
                                                           collection)
            return 'server', res_token, items
        else:
            log.debug("Does not support server side pagination. Client will"
                      " limit and page results.")
            return 'client', None, collection

    def list(self, limit=None, marker=None, collection=None, **kwargs):
        """
        List a set of resources.

        :type  collection: ``ResourceCollection``
        :param collection: Boto resource collection object corresponding to the
                           current resource. See http://boto3.readthedocs.io/
                           en/latest/guide/collections.html
        """
        limit = limit or self.provider.config.default_result_limit
        collection = collection or self.boto_collection.filter(**kwargs)
        pag_type, resume_token, boto_objs = self._make_query(collection,
                                                             limit,
                                                             marker)
        # Wrap in CB objects.
        results = [self.cb_resource(self.provider, obj) for obj in boto_objs]

        if pag_type == 'server':
            log.debug("Using server pagination.")
            return ServerPagedResultList(is_truncated=True if resume_token
                                         else False,
                                         marker=resume_token if resume_token
                                         else None,
                                         supports_total=False,
                                         data=results)
        else:
            log.debug("Did not received a resume token, will page in client"
                      " if necessary.")
            return ClientPagedResultList(self.provider, results,
                                         limit=limit, marker=marker)

    def find(self, filter_name, filter_value, limit=None, marker=None,
             **kwargs):
        """
        Return a list of resources by filter.

        :type filter_name: ``str``
        :param filter_name: Name of the filter to use

        :type filter_value: ``str``
        :param filter_value: Value to filter with
        """
        collection = self.boto_collection
        collection = collection.filter(Filters=[{
            'Name': filter_name,
            'Values': [filter_value]
            }])
        if kwargs:
            collection = collection.filter(**kwargs)
        return self.list(limit=limit, marker=marker, collection=collection)

    def create(self, boto_method, **kwargs):
        """
        Creates a resource

        :type boto_method: ``str``
        :param boto_method: AWS Service method to invoke

        :type kwargs: ``dict``
        :param kwargs: Arguments to be passed as-is to the service method
        """
        log.debug("Creating a resource by invoking %s on these arguments: %s",
                  boto_method, kwargs)
        trimmed_args = trim_empty_params(kwargs)
        result = getattr(self.boto_conn, boto_method)(**trimmed_args)
        if isinstance(result, list):
            return [self.cb_resource(self.provider, obj)
                    for obj in result if obj]
        else:
            return self.cb_resource(self.provider, result) if result else None

    def delete(self, resource_id):
        """
        Deletes a resource by id

        :type resource_id: ``str``
        :param resource_id: ID of the resource
        """
        log.info("Delete the resource with the id %s", resource_id)
        res = self.get(resource_id)
        if res:
            res.delete()


class BotoEC2Service(BotoGenericService):
    """
    Boto EC2 service implementation
    """
    def __init__(self, provider, cb_resource,
                 boto_collection_name):
        """
        :type provider: :class:`AWSCloudProvider`
        :param provider: CloudBridge AWS provider to use

        :type cb_resource: :class:`CloudResource`
        :param cb_resource: CloudBridge Resource class to wrap results in

        :type boto_collection_name: ``str``
        :param boto_collection_name: Boto collection name that corresponds
                                    to the CloudBridge resource (e.g. key_pair)
        """
        super(BotoEC2Service, self).__init__(
            provider, cb_resource, provider.ec2_conn,
            boto_collection_name)


class BotoS3Service(BotoGenericService):
    """
    Boto S3 service implementation.
    """
    def __init__(self, provider, cb_resource,
                 boto_collection_name):
        """
        :type provider: :class:`AWSCloudProvider`
        :param provider: CloudBridge AWS provider to use

        :type cb_resource: :class:`CloudResource`
        :param cb_resource: CloudBridge Resource class to wrap results in

        :type boto_collection_name: ``str``
        :param boto_collection_name: Boto collection name that corresponds
                                    to the CloudBridge resource (e.g. key_pair)
        """
        super(BotoS3Service, self).__init__(
            provider, cb_resource, provider.s3_conn,
            boto_collection_name)
