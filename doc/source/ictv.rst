.. include:: links.rst

ICTV Plugin
===========

How to setup local testing ICTV server ?
----------------------------------------

The installation and the configuration of a local instance of ICTV is quite an easy task.


virtualenv
~~~~~~~~~~

It's just recommended to use a virtualenv_ in order to keep your distro clean.

.. role:: bash(code)
   :language: bash

Here is the simplier way to use virtualenv :

- Create new virtualenv

      :bash:`virtualenv --python=<path_to_python_install> <env_name>` 

- Activate the environment

      :bash:`source <env_name>/bin/activate`

- Closing the environment

      :bash:`deactivate`

Installing ICTV
~~~~~~~~~~~~~~~

Once the virtualenv_ is created and activated, you can `install ictv`_ using pip. 
The `minimal development configuration file`_ is also given.

Just follow the instructions on the given pages in order to get the ICTV instance up.

Configuration
~~~~~~~~~~~~~

Now you need to add some channels. 

In order to do this, you first have to activate the plugins that you need. For the current 
Superform version, we only support the **editor** plugin.
You can achieve this task on the `Plugins` tab on the left menu.

On the `Channels` tab you can manage the channels as you want. In order to be able to use 
the REST API, you have to tick the `Enable the REST API` box and add a secure key.

*That's it*

You now have a development instance of ICTV ready to get your wonderful slides !

.. _virtualenv: https://virtualenv.pypa.io/en/latest/
.. _install ictv: https://ictv.readthedocs.io/en/latest/install_ictv.html#installing-ictv
.. _minimal development configuration file: https://ictv.readthedocs.io/en/latest/dev_environment.html#setting-up
