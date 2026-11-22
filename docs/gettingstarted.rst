Getting Started
===============

Installation
------------
To install python-amcards, simply run this command in your terminal:

.. code-block::

    $ pip install python-amcards

Usage
-----
All interactions with the AMcards API are made through the :ref:`AMcardsClient <amcards.AMcardsClient>` class.

First, create an :ref:`AMcardsClient <amcards.AMcardsClient>` as follows:

.. code-block::

    >>> from amcards import AMcardsClient
    >>> client = AMcardsClient('youraccesstoken')

Here ``'youraccesstoken'`` will be replaced with a string containing your AMcards access token. You can generate one `here <https://amcards.com/user/generate-access-token/>`_.

Now we can perform all operations supported by the :ref:`client <amcards.AMcardsClient>`.

Let's try using ``send_card`` to send a card to a single recipient:

.. code-block::

        >>> res = client.send_card(
        ...     template_id='123',
        ...     initiator='myintegration123',
        ...     shipping_address={
        ...         'first_name': 'Ralph',
        ...         'last_name': 'Mullins',
        ...         'address_line_1': '2285 Reppert Road',
        ...         'city': 'Southfield',
        ...         'state': 'MI',
        ...         'postal_code': '48075',
        ...         'country': 'US'
        ...     }
        ... )
        >>> res.card_id
        1522873
        >>> res.total_cost
        442
        >>> res.message
        'Card created successfully!'
        >>> res.user_email
        'example@example.com'
        >>> res.shipping_address
        {'last_name': 'Mullins', 'address_line_1': '2285 Reppert Road', 'first_name': 'Ralph', 'country': 'US', 'state': 'MI', 'postal_code': '48075', 'city': 'Southfield'}

Request timeouts and tracking
-----------------------------
Configure a timeout once for every request, including OAuth token refreshes:

.. code-block:: python

    client = AMcardsClient('youraccesstoken', timeout=(3, 6))
    cards = client.cards(limit=1, filters={'third_party_contact_id': 'customer-123'})
    tracking_number = cards[0].tracking_id if cards else None

The tuple means a 3-second connection timeout and a 6-second read timeout between
incoming data. It is not a total operation deadline. A single number applies to
both. The default is ``None``, preserving the previous behavior with no timeout.
Every API method accepts a ``timeout`` override; omitting it or passing ``None``
uses the client setting:

.. code-block:: python

    cards = client.cards(limit=1, timeout=(3, 15))

Requests timeout exceptions propagate to the caller. The client does not retry
requests automatically; a timeout during a send does not establish whether the
server completed it.

``Card.tracking_id`` is ``None`` for absent or empty tracking identifiers.
Custom card metadata remains available through ``Card.extra_data``, and query
filters continue to use the existing ``filters`` dictionary.
