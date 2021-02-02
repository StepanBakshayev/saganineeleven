===================================
Saganineeleven [Norén is on Porshe]
===================================

Warning
=======

This product is for developers. The library handle variable substitution, condition evaluation, loop iteration. Power comes with responsibility.
End user should be aware of implementation details and format specification to get correct result.
Anyway it depends on concrete template. Some users don't fill any difficulties from ordinary template.


Usage
=====


Library
-------


.. code-block:: python

    from saganineeleven import render
    from saganineeleven import contrib

    render(
        open('source_file.docx', 'rb'),
        open('destination_file.docx', 'wb'),
        contrib.docx,
        contrib.django,
        {"var1": "Hello,", "var2": ["Prince", 0]}
    )


CLI
---

.. code-block:: sh

    $ saganineeleven --source case_03.docx --destination case_rendered.docx --document-handler docx --template-handler django --context '{"var1": "Hello,", "var2": ["Prince", 0]}'


Licence
=======

Saganineeleven is distributed under the terms of LGPLv3.

See COPYING.LESSER.

There is another option to buy commercial licence. Sent request to contact <<sign for electronic mail delimeter>> teasonyou.id.
