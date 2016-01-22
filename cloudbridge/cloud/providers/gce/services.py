from cloudbridge.cloud.base.services import BaseSecurityService


class GCESecurityService(BaseSecurityService):

    def __init__(self, provider):
        super(GCESecurityService, self).__init__(provider)
