.. _dms2_batch_bcsubamp:

==========================================
``dms2_batch_bcsubamp``
==========================================

.. contents::
   :local:

Overview
-------------
The ``dms2_batch_bcsubamp`` program processes FASTQ files generated by :ref:`bcsubamp` to count the frequencies of mutations at each site for a set of samples, and then summarize the results.

The ``dms2_batch_bcsubamp`` program simply runs :ref:`dms2_bcsubamp` for each sample listed in a batch file specified by ``--batchfile``.
Specifically, as described in :ref:`batch_bcsubamp_commandlineusage`, you can specify a few sample-specific arguments in the ``--batchfile``.
All other arguments are specified using the normal option syntax (e.g., ``--bclen BCLEN``) and are shared between all samples specified in ``--batchfile``.
The result is the output for each individual run of :ref:`dms2_bcsubamp` plus the summary plots described in `Output files`_.

The `Doud2016 example`_ to illustrates the usage of ``dms2_batch_bcsubamp`` on a real dataset.

Because ``dms2_batch_bcsubamp`` simply runs ``dms2_bcsubamp`` on each sample specfied by the ``--batchfile`` argument described below, see the ``dms2_bcsubamp`` :ref:`bcsubamp_algorithm` and the ``dms2_bcsubamp`` :ref:`bcsubamp_commandlineusage` for details that are helpful for understanding many of the arguments in the ``dms2_batch_bcsubamp`` :ref:`batch_bcsubamp_commandlineusage` below.

.. _batch_bcsubamp_commandlineusage:

Command-line usage
---------------------------------------------

.. argparse::
   :module: dms_tools2.parseargs
   :func: batch_bcsubampParser
   :prog: dms2_batch_bcsubamp

   \-\-summaryprefix
    As detailed in `Output files` below, ``dms2_batch_bcsubamp`` creates a variety of plots summarizing the output.
    These files are in the directory specified by ``--outdir``, and have the prefix specified here.
    This prefix should only contain letters, numbers, dashes, and spaces.
    Underscores are **not** allowed as they are a LaTex special character.

   \-\-ncpus
    Multiple runs of ``dms2_bcsubamp`` can be performed in parallel on the different samples specified by ``--batchfile``. 
    This argument determines how many CPUs are used if running multiple jobs.

Output files
--------------
Running ``dms2_batch_bcsubamp`` produces a variety of output files, all of which will be found in the directory specified by ``--outdir``.

Results for each sample
++++++++++++++++++++++++++
The program ``dms2_bcsubamp`` is run on each sample specified by ``--batchfile``, so you will create all of the ``dms2_bcsubamp`` :ref:`bcsubamp_outputfiles`.

Summary files
++++++++++++++++
Plots are created that summarize the output for all samples specified by ``--batchfile``. 
These samples have the prefix specified by ``--summaryprefix``. 
So for instance, if you run ``dms2_batch_bcsubamp`` with the arguments ``--outdir results --summaryprefix summary`` then these files will have the prefix ``./results/summary``.
They will have the suffixes listed below:

    * ``.log``: a text file that logs the progress of the program.

    * ``_readstats.pdf``: plot of reads for each sample.

    * ``_bcstats.pdf``: plot of barcodes for each sample.

    * ``_readsperbc.pdf``: plot of distribution of the number of reads per-barcode for each sample.

    * ``_depth.pdf``: plot of number of counts called at each site for each sample.

    * ``_mutfreq.pdf``: plot of mutation frequency at each site for each sample.

    * ``_codonmuttypes.pdf``: plot of average frequency of different types of codon mutations.

    * ``_codonmuttypes.csv``: numerical data in ``_codonmuttypes.pdf``.

    * ``_codnntchanges.pdf``: plot of average frequency of codon mutations with different numbers of nucleotide changes.

    * ``_singlentchanges.pdf``: plot frequencies of different types of nucleotide mutations among codons with just one nucleotide change.

    * ``_cumulmutcounts.pdf``: plot fraction of mutations that occur :math:`\leq` a given number of times.

Examples and more detailed explanations of these plots can be found in the `Doud2016 example`_.

Memory usage
---------------------------
As described in the :ref:`bcsubamp_memoryusage` section for ``dms2_bcsubamp``, each iteration of that program can consume substantial memory.
So obviously running it multiple times in parallel with ``dms2_batch_bcsubamp`` will consume even more memory.

.. include:: weblinks.txt
