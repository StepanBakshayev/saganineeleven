==============
Saganineeleven
==============


Abstract
========

People use docx, odt as desktop typographical. It is compleatly wrong, it is doing it job.
I used libreoffice in an university for markup result of my work. There are more suitable systems for markup. For example, Latex.
Things get more worse when business make decesion to use docx, odt in auto-generating document else with templates. I give advice to Latex again in this situation too. This is not taken into consideration.
Well, we are developers, take issue and put job on table!

In speaking of Latex there is lightweight option. You combine pseudo-graphics text format like wiki, markdown, restructured text with document generator like `pandoc <https://pandoc.org/>`_.
It is not issue to feed your favorite template engine with text, next the output is sending to renderer.

So, you do not turn with rational solution and stay here for docx, odt templating. Move on.


Design
======


The problem
-----------

<Manager suppose to using UI by broad audience. People put template constructs between xml tags as editing in UI. Templete engine is useless.>


Implementation on market
------------------------


Using spicial tags on tags
^^^^^^^^^^^^^^^^^^^^^^^^^^

- https://habr.com/ru/post/269307/ (C#)
- https://pypi.org/project/docx-mailmerge/ (Python)


The verdict
"""""""""""

This is not templating. It is puting only. You can not use conditions. You should know shape of data structures to guess result.
Else UI is using heavy.


Using comments with code
^^^^^^^^^^^^^^^^^^^^^^^^

- http://www.appyframework.org/pod.html

It is variant of spicial tags but with comments and upgrade with using code to manipulate output.


The verdict
"""""""""""

It is php in document.
Very hight the entry threshold.
Else UI is using heavy.


Announce jinja2, implementing hack on top
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- https://github.com/elapouya/python-docx-template

It is scam. Like any other scam It is feeded by people.

There are more. I fill the list in future.


Honestly announce hacks as templating
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- https://docxtemplater.com/ (js)


The verdict
"""""""""""

It is much closer to templating then anything.
You should buy more hacks.


Other things to investigate
^^^^^^^^^^^^^^^^^^^^^^^^^^^

- https://www.tinybutstrong.com/opentbs.php


Goals
-----

- do not touch template engine, use it as is
- make behaviour of templates tags inside hierarchical structure (XML) as natural as possible, prevent wrong places of tags


Licence
=======

Saganineeleven is distributed under the terms of LGPLv3.

See COPYING.LESSER.

There is another option to buy commercial licence. Sent request to contact <<sign for electronic mail delimeter>> teasonyou.id.
