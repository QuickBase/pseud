Authentication
==============

pseud allows you to build your own Authentication Backend.
Your implementation must conform to its
:py:class:`Interface <zope.interface.Interface>` defined in
:py:class:`pseud.interfaces.IAuthenticationBackend`

Also all your plugin must :py:func:`adapts <zope.component.adapts>` :py:class:`pseud.interfaces.IClient` or
:py:class:`pseud.interfaces.IServer` and being registered thanks to
:py:func:`pseud.utils.register_auth_backend` decorator.

Implementing your own authentication backend can be used to support
CURVE encryption. And also for more advanced use-case with external ID provider.
That is your favorite web-framework or simple PAM, you name it.

You can start with the following snippet ::

    @register_auth_backend
    @zope.interface.implementer(IAuthenticationBackend)
    @zope.component.adapter(IClient)
    class MyAuthenticationBackend(object):
        """
        This implementation implements
        IAuthenticationBackend and adapts IClient
        """
        name = 'my_auth_backend'

        def __init__(self, rpc):
            self.rpc = rpc

        async def stop(self):
            pass

        def configure(self):
            pass

        async def handle_hello(self, *args):
            pass

        async def handle_authenticated(self, message):
            pass

        async def is_authenticated(self, user_id):
            return True

        def save_last_work(self, message):
            pass

        def get_predicate_arguments(self, user_id):
            return {}

In this example the name `'my_auth_backend'` will be used when instanciating
your RPC endpoint.

.. code:: python

    client = pseud.Client('remote',
                          security_plugin='my_auth_backend')


Read :ref:`protocol` for more explanation. Also in :mod:`pseud.auth` you will find
examples that are used in tests.
