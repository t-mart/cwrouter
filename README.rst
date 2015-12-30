******************************************************
cwrouter: uploading my network usage to AWS CloudWatch
******************************************************

cwrouter relays network usage statistics from my home router to `Amazon
CloudWatch <https://aws.amazon.com/cloudwatch/>`_.

Run via a scheduled job (e.g. cron), every 5 minutes, cwrouter
checks my routers administrator web page, scrapes statistics from it, and
uploads them to CloudWatch with boto. From CloudWatch, I can monitor,
analyze and alarm on my usage of my service provider's plan (200GB
combined upload and download per month). This allows me to avoid
fees I might be charged if I were to exceed this allotment.

.. image:: http://i.imgur.com/PuWuG5Y.png
    :alt: cwrouter statistics viewed on the CloudWatch web console
    :align: center


Stats
#####

cwrouter knows how to grab/calculate the following stats:

* *recv_bytes*: The number of bytes received by the router
* *sent_bytes*: The number of bytes sent by the router
* *total_bytes*: The sum of the above
* *recv_sent_rate*: The number of bytes received for each byte sent

As of now, cwrouter only knows how to scrape my router model's admin web page.
It is an **Arris NVG599**. But there's no reason it can't upload yours with
modification.

Installation
############

Clone the repo and then install it with pip:

.. code-block:: bash

    $ git clone https://github.com/t-mart/cwrouter.git

    $ pip install --upgrade cwrouter

*(Optional)* To test cwrouter, run **make**.

Configuration
#############

Run cwrouter once to create a skeleton configuration file. The output will
tell you where cwrouter stored this skeleton file. It is plain JSON.

.. code-block:: bash

    $ cwrouter
    cwrouter is stopping because you have no config! skeleton written to /home/tim/.cwrouter/config.json. fill in your credentials.


Edit it to include your AWS credentials.

Job Scheduling
**************

cwrouter only uploads statistics when it's run! Scheduled execution is
delegated to your preference of system job scheduler, such as cron or the
Windows Task Scheduler. Refer to your respective documentation.

I set cwrouter to run every 5 minutes.

CloudWatch
**********

cwrouter router uploads its data under the "cwrouter" namespace, but you can
change that in the config if you'd like.

You may also want to set up an alarm if you exceed a certain rate.
