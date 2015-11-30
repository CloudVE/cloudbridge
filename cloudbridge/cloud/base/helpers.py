class TestMockHelperMixin(object):
    """
    A helper class that providers mock drivers can use to be notified when a
    test setup/teardown occurs. This is useful when activating libraries
    like HTTPretty which take over socket communications.
    """

    def setUpMock(self):
        """
        Called before a test is started.
        """
        raise NotImplementedError(
            'TestMockHelperMixin.setUpMock not implemented')

    def tearDownMock(self):
        """
        Called before test teardown.
        """
        raise NotImplementedError(
            'TestMockHelperMixin.tearDownMock not implemented by this'
            ' provider')
