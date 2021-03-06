"""
===================
plot
===================

Plotting functions for ``dms_tools2``.

Uses `plotnine <https://plotnine.readthedocs.io/en/stable>`_
and `seaborn <https://seaborn.pydata.org/index.html>`_.
"""


import re
import os
import math
import natsort
import pandas
import numpy
import scipy.stats
import matplotlib
matplotlib.use('pdf')
import matplotlib.pyplot as plt

from plotnine import *
# set ggplot theme
theme_set(theme_bw(base_size=12)) 

import seaborn
seaborn.set(context='talk',
            style='white',
            rc={
                'xtick.labelsize':15,
                'ytick.labelsize':15,
                'axes.labelsize':19,
                'font.family':'sans-serif',
                'font.sans-serif':['DejaVu Sans'],
                }
           )

from dms_tools2 import CODONS, AAS, AAS_WITHSTOP
import dms_tools2.utils

#: `color-blind safe palette <http://bconnelly.net/2013/10/creating-colorblind-friendly-figures/>`_
#: use by adding to your plots the following
#: `scale_fill_manual(COLOR_BLIND_PALETTE)` or
#: `scale_color_manual(COLOR_BLIND_PALETTE)`.
COLOR_BLIND_PALETTE = ["#000000", "#E69F00", "#56B4E9", "#009E73",
                       "#F0E442", "#0072B2", "#D55E00", "#CC79A7"]


def breaksAndLabels(xi, x, n):
    """Get breaks and labels for an axis.

    Useful when you would like to re-label a numeric x-axis
    with string labels.

    Uses `matplotlib.ticker.MaxNLocator` to choose pretty breaks.

    Args:
        `xi` (list or array)
            Integer values actually assigned to axis points.
        `x` (list)
            Strings corresponding to each numeric value in `xi`.
        `n` (int)
            Approximate number of ticks to use.

    Returns:
        The tuple `(breaks, labels)` where `breaks` gives the
        locations of breaks taken from `xi`, and `labels` is
        the label for each break.

    >>> xi = list(range(213))
    >>> x = [str(i + 1) for i in xi]
    >>> (breaks, labels) = breaksAndLabels(xi, x, 5)
    >>> breaks
    [0, 50, 100, 150, 200]
    >>> labels
    ['1', '51', '101', '151', '201']
    """
    assert len(xi) == len(x)
    assert all([isinstance(i, (int, numpy.integer)) for i in xi]), \
            "xi not integer values:\n{0}".format(xi)
    xi = list(xi)
    assert sorted(set(xi)) == xi, "xi not unique and ordered"
    breaks = matplotlib.ticker.MaxNLocator(n).tick_values(xi[0], xi[-1])
    breaks = [int(i) for i in breaks if xi[0] <= i <= xi[-1]]
    labels = [x[xi.index(i)] for i in breaks]
    return (breaks, labels)


def latexSciNot(xlist):
    """Converts list of numbers to LaTex scientific notation.

    Useful for nice axis-tick formatting.

    Args:
        `xlist` (list)
            Numbers to format.

    Returns:
        List of latex scientific notation formatted strings.

    >>> latexSciNot([0, 3, 3120, -0.0000927])
    ['$0$', '$3$', '$3.1 \\\\times 10^{3}$', '$-9.3 \\\\times 10^{-5}$']

    >>> latexSciNot([0.001, 1, 1000, 1e6])
    ['$0.001$', '$1$', '$10^{3}$', '$10^{6}$']

    >>> latexSciNot([-0.002, 0.003, 0.000011])
    ['$-0.002$', '$0.003$', '$1.1 \\\\times 10^{-5}$']

    >>> latexSciNot([-0.1, 0.0, 0.1, 0.2])
    ['$-0.1$', '$0$', '$0.1$', '$0.2$']

    >>> latexSciNot([0, 1, 2])
    ['$0$', '$1$', '$2$']
    """
    formatlist = []
    for x in xlist:
        xf = "{0:.2g}".format(x)
        if xf[ : 2] == '1e':
            xf = "$10^{{{0}}}$".format(int(xf[2 : ]))
        elif xf[ : 3] == '-1e':
            xf = "$-10^{{{0}}}$".format(int(xf[3 : ]))
        elif 'e' in xf:
            (d, exp) = xf.split('e')
            xf = '${0} \\times 10^{{{1}}}$'.format(d, int(exp))
        else:
            xf = '${0}$'.format(xf)
        formatlist.append(xf)
    return formatlist


def plotReadStats(names, readstatfiles, plotfile):
    """Plots ``dms2_bcsubamp`` read statistics for a set of samples.
    
    Args:
        `names` (list or series)
            Names of the samples for which we are plotting statistics.
        `readstatfiles` (list or series)
            Names of ``*_readstats.csv`` files created by ``dms2_bcsubamp``.
        `plotfile` (str)
            Name of PDF plot file to create.
    """
    assert len(names) == len(readstatfiles) == len(set(names))
    assert os.path.splitext(plotfile)[1].lower() == '.pdf'
    readstats = pandas.concat([pandas.read_csv(f).assign(name=name) for
                (name, f) in zip(names, readstatfiles)], ignore_index=True)
    readstats['retained'] = (readstats['total'] - readstats['fail filter']
            - readstats['low Q barcode'])
    readstats_melt = readstats.melt(id_vars='name', 
            value_vars=['retained', 'fail filter', 'low Q barcode'],
            value_name='number of reads', var_name='read fate')
    p = (ggplot(readstats_melt)
            + geom_col(aes(x='name', y='number of reads', fill='read fate'),
                position='stack')
            + theme(axis_text_x=element_text(angle=90, vjust=1, hjust=0.5),
                    axis_title_x=element_blank()) 
            + scale_y_continuous(labels=latexSciNot) 
            + scale_fill_manual(COLOR_BLIND_PALETTE)
            )
    p.save(plotfile, height=2.7, width=(1.2 + 0.25 * len(names)),
            verbose=False)
    plt.close()


def plotBCStats(names, bcstatsfiles, plotfile):
    """Plots ``dms2_bcsubamp`` barcode statistics for set of samples.

    Args:
        `names` (list or series)
            Names of the samples for which we are plotting statistics.
        `bcstatsfiles` (list or series)
            Names of ``*_bcstats.csv`` files created by ``dms2_bcsubamp``.
        `plotfile` (str)
            Name of PDF plot file to create.
    """
    assert len(names) == len(bcstatsfiles) == len(set(names))
    assert os.path.splitext(plotfile)[1].lower() == '.pdf'
    bcstats = pandas.concat([pandas.read_csv(f).assign(name=name) for
                (name, f) in zip(names, bcstatsfiles)], ignore_index=True)
    bcstats_melt = bcstats.melt(id_vars='name', 
            value_vars=['too few reads', 'not alignable', 'aligned'],
            value_name='number of barcodes', var_name='barcode fate')
    p = (ggplot(bcstats_melt)
            + geom_col(aes(x='name', y='number of barcodes', 
                fill='barcode fate'), position=position_stack(reverse=True))
            + theme(axis_text_x=element_text(angle=90, vjust=1, hjust=0.5),
                    axis_title_x=element_blank())
            + scale_y_continuous(labels=latexSciNot)
            + scale_fill_manual(COLOR_BLIND_PALETTE)
            )
    p.save(plotfile, height=2.7, width=(1.2 + 0.25 * len(names)),
            verbose=False)
    plt.close()


def plotReadsPerBC(names, readsperbcfiles, plotfile, 
        maxreads=10, maxcol=6):
    """Plots ``dms2_bcsubamp`` reads-per-barcode stats for set of samples.

    Args:
        `names` (list or series)
            Names of samples for which we plot statistics.
        `readsperbcfiles` (list or series)
            Names of ``*_readsperbc.csv`` files created by ``dms2_bcsubamp``.
        `plotfile` (str)
            Name of PDF plot file to create.
        `maxreads` (int)
            For any barcodes with > this many reads, just make a category
            of >= this.
        `maxcol` (int)
            Number of columns in faceted plot.
    """
    assert len(names) == len(readsperbcfiles) == len(set(names))
    assert os.path.splitext(plotfile)[1].lower() == '.pdf'

    # read data frames, ensure 'number of reads' from 1 to >= maxreads
    dfs = []
    for (name, f) in zip(names, readsperbcfiles):
        df = pandas.read_csv(f)
        # make 'number of reads' maxreads hold number >= maxreads barcodes
        n_ge = df[df['number of reads'] >= maxreads]['number of reads'].sum()
        df = df.append(pandas.DataFrame({'number of reads':[maxreads],
                'number of barcodes':[n_ge]}))
        for nreads in range(1, maxreads):
            if nreads not in df['number of reads']:
                df.append(pandas.DataFrame({'number of reads':[nreads],
                        'number of barcodes':[0]}))
        df = df[df['number of reads'] <= maxreads]
        df = df.assign(name=name)
        dfs.append(df)
    df = pandas.concat(dfs, ignore_index=True)

    # make name a category to preserve order
    df['name'] = df['name'].astype('category', categories=names)

    ncol = min(maxcol, len(names))
    nrow = math.ceil(len(names) / float(ncol))
    p = (ggplot(df)
            + geom_col(aes(x='number of reads', y='number of barcodes'),
                position='stack')
            + scale_x_continuous(breaks=[1, maxreads // 2, maxreads],
                    labels=['$1$', '${0}$'.format(maxreads // 2), 
                    '$\geq {0}$'.format(maxreads)])
            + scale_y_continuous(labels=latexSciNot)
            + facet_wrap('~name', ncol=ncol)
            + theme(figure_size=(1.9 * (0.8 + ncol), 1.3 * (0.4 + nrow)))
            )
    p.save(plotfile, verbose=False)
    plt.close()


def plotDepth(names, countsfiles, plotfile, maxcol=4, charlist=CODONS):
    """Plot sequencing depth along primary sequence.

    Args:
        `names` (list or series)
            Names of samples for which we plot statistics.
        `countsfiles` (list or series)
            Files containing character counts at each site.
            Should have column named `site` and a column
            for each character in `charlist`.
        `plotfile` (str)
            Name of created PDF plot file containing count depth.
        `maxcol` (int)
            Number of columns in faceted plot.
        `charlist` (list)
            Characters contained in `countsfiles`. For instance,
            list of codons or amino acids.
    """
    assert len(names) == len(countsfiles) == len(set(names))
    assert os.path.splitext(plotfile)[1].lower() == '.pdf'

    counts = pandas.concat(
            [pandas.read_csv(f)
                   .assign(name=name)
                   .assign(ncounts=lambda x: x[charlist].sum(axis=1))
                   .rename(columns={'ncounts':'number of counts'})
            for (name, f) in zip(names, countsfiles)], ignore_index=True)
    
    ncol = min(maxcol, len(names))
    nrow = math.ceil(len(names) / float(ncol))

    # make name a category to preserve order
    counts['name'] = counts['name'].astype('category', 
            categories=names)

    p = (ggplot(counts, aes(x='site', y='number of counts'))
            + geom_step(size=0.4)
            + scale_y_continuous(labels=latexSciNot, 
                    limits=(0, counts['number of counts'].max()))
            + scale_x_continuous(limits=(counts['site'].min(),
                    counts['site'].max()))
            + facet_wrap('~name', ncol=ncol) 
            + theme(figure_size=(2.25 * (0.6 + ncol), 1.3 * (0.3 + nrow)))
            )
    p.save(plotfile, verbose=False)
    plt.close()


def plotMutFreq(names, countsfiles, plotfile, maxcol=4):
    """Plot mutation frequency along primary sequence.

    Args:
        `names` (list or series)
            Names of samples for which we plot statistics.
        `countsfiles` (list or series)
            ``*_codoncounts.csv`` files of type created by ``dms2_bcsubamp``.
        `plotfile` (str)
            Name of created PDF plot file.
        `maxcol` (int)
            Number of columns in faceted plot.
    """
    assert len(names) == len(countsfiles) == len(set(names))
    assert os.path.splitext(plotfile)[1].lower() == '.pdf'

    counts = pandas.concat([dms_tools2.utils.annotateCodonCounts(f).assign(
            name=name) for (name, f) in zip(names, countsfiles)], 
            ignore_index=True).rename(columns={'mutfreq':'mutation frequency'})
    
    ncol = min(maxcol, len(names))
    nrow = math.ceil(len(names) / float(ncol))

    # make name a category to preserve order
    counts['name'] = counts['name'].astype('category', 
            categories=names)

    p = (ggplot(counts, aes(x='site', y='mutation frequency'))
            + geom_step(size=0.4)
            + scale_y_continuous(labels=latexSciNot, 
                    limits=(0, counts['mutation frequency'].max()))
            + scale_x_continuous(limits=(counts['site'].min(),
                    counts['site'].max()))
            + facet_wrap('~name', ncol=ncol) 
            + theme(figure_size=(2.25 * (0.6 + ncol), 1.3 * (0.3 + nrow)))
            )
    p.save(plotfile, verbose=False)
    plt.close()


def plotCumulMutCounts(names, countsfiles, plotfile, chartype,
        nmax=15, maxcol=6):
    """Plot fraction of mutations seen <= some number of times.

    For each set of counts in `countsfiles`, plot the fraction
    of mutations seen greater than or equal to some number of
    times. This is essentially a cumulative fraction plot.

    Args:
        `names` (list or series)
            Names of samples for which we plot statistics.
        `countsfiles` (list or series)
            ``*_codoncounts.csv`` files of type created by ``dms2_bcsubamp``.
        `plotfile` (str)
            Name of created PDF plot file.
        `chartype` (str)
            The type of character in `countsfiles`.

                - `codon` 

        `nmax` (int)
            Plot out to this number of mutation occurrences.
        `maxcol` (int)
            Number of columns in faceted plot.
    """
    assert len(names) == len(countsfiles) == len(set(names))
    assert os.path.splitext(plotfile)[1].lower() == '.pdf'

    counts = pandas.concat([pandas.read_csv(f).assign(name=name) for
            (name, f) in zip(names, countsfiles)], ignore_index=True)

    if chartype != 'codon':
        raise ValueError("invalid chartype of {0}".format(chartype))

    codoncounts = pandas.concat([pandas.read_csv(f).assign(name=name)
            for (name, f) in zip(names, countsfiles)],
            ignore_index=True).assign(character='codons')
    assert set(CODONS) <= set(codoncounts.columns)
    codonmelt = codoncounts.melt(id_vars=['name', 'wildtype', 'character'], 
            value_vars=CODONS, value_name='counts',
            var_name='codon')
    codonmelt = codonmelt[codonmelt['codon'] != codonmelt['wildtype']]

    aacounts = pandas.concat([dms_tools2.utils.codonToAACounts(
            pandas.read_csv(f)).assign(name=name)
            for (name, f) in zip(names, countsfiles)],
            ignore_index=True).assign(character='amino acids')
    assert set(AAS_WITHSTOP) <= set(aacounts.columns)
    aamelt = aacounts.melt(id_vars=['name', 'character', 'wildtype'], 
            value_vars=AAS_WITHSTOP, value_name='counts',
            var_name='aa')
    aamelt = aamelt[aamelt['aa'] != aamelt['wildtype']]

    df = pandas.concat([codonmelt, aamelt], ignore_index=True)

    # make name a category to preserve order
    df['name'] = df['name'].astype('category', categories=names)

    maxcol = 4
    ncol = min(maxcol, len(names))
    nrow = math.ceil(len(names) / float(ncol))
    p = (ggplot(df, aes('counts', color='character', linestyle='character'))
            + stat_ecdf(geom='step', size=1)
            + scale_x_continuous(limits=(0, nmax))
            + facet_wrap('~name', ncol=ncol) 
            + theme(figure_size=(2.25 * (0.6 + ncol), 1.3 * (0.5 + nrow)),
                    legend_position='top', legend_direction='horizontal')
            + labs(color="") 
            + guides(color=guide_legend(title_position='left'))
            + ylab('fraction $\leq$ this many counts')
            + scale_color_manual(COLOR_BLIND_PALETTE)
            )
    p.save(plotfile, verbose=False)
    plt.close()


def plotCodonMutTypes(names, countsfiles, plotfile,
        classification='aachange', csvfile=None):
    """Plot average frequency codon mutation types.

    The averages are determined by summing counts for all sites.

    Args:
        `names` (list or series)
            Names of samples for which we plot statistics.
        `countsfiles` (list or series)
            ``*_codoncounts.csv`` files of type created by ``dms2_bcsubamp``.
        `plotfile` (str)
            Name of created PDF plot file.
        `classification` (str)
            The method used to classify the mutation types. Can be:

                `aachange` : stop, synonymous, nonsynonymous

                `n_ntchanges` : number of nucleotide changes per codon

                `singlentchanges` : nucleotide change in 1-nt mutations

        `csvfile` (str or `None`)
            `None` or name of CSV file to which numerical data are written.
    """
    assert len(names) == len(countsfiles) == len(set(names))
    assert os.path.splitext(plotfile)[1].lower() == '.pdf'

    counts = pandas.concat([dms_tools2.utils.annotateCodonCounts(f).assign(
            name=name) for (name, f) in zip(names, countsfiles)], 
            ignore_index=True)

    if classification == 'aachange':
        muttypes = {'stop':'nstop', 'synonymous':'nsyn', 
                'nonsynonymous':'nnonsyn'}
    elif classification == 'n_ntchanges':
        muttypes = dict([('{0} nucleotide'.format(n), 'n{0}nt'.format(n))
                for n in [1, 2, 3]])
    elif classification == 'singlentchanges':
        muttypes = dict([(ntchange, ntchange) for ntchange in [
                '{0}to{1}'.format(nt1, nt2) for nt1 in dms_tools2.NTS
                for nt2 in dms_tools2.NTS if nt1 != nt2]])
    else:
        raise ValueError("Invalid classification {0}".format(classification))

    df = (counts[list(muttypes.values()) + ['ncounts', 'name']]
            .groupby('name', as_index=False)
            .sum(axis=1)
            .assign(ncounts=lambda x: x['ncounts'].astype('float'))
            )
    for (newcol, n) in muttypes.items():
        df[newcol] = (df[n] / df['ncounts']).fillna(0)

    if csvfile:
        df[['name'] + list(muttypes.keys())].to_csv(csvfile, index=False) 

    df = df.melt(id_vars='name', var_name='mutation type',
                value_vars=list(muttypes.keys()),
                value_name='per-codon frequency')

    p = (ggplot(df)
            + geom_col(aes(x='name', y='per-codon frequency', 
                fill='mutation type'), position='stack')
            + theme(axis_text_x=element_text(angle=90, vjust=1, hjust=0.5),
                    axis_title_x=element_blank())
            + scale_y_continuous(labels=latexSciNot)
            )
    if len(muttypes) <= len(COLOR_BLIND_PALETTE):
        p += scale_fill_manual(COLOR_BLIND_PALETTE)
    else:
        p += guides(fill=guide_legend(ncol=2))

    p.save(plotfile, height=2.7, width=(1.2 + 0.25 * len(names)),
            verbose=False)
    plt.close()


def plotCorrMatrix(names, infiles, plotfile, datatype,
        trim_unshared=True, title=''):
    """Plots correlations among replicates.

    Args:
        `names` (list or series)
            Names of samples for which we plot statistics.
        `infiles` (list or series)
            CSV files containing data. Format depends on `datatype`.
        `plotfile` (str)
            Name of created PDF plot file.
        `datatype` (str)
            Type of data for which we are plotting correlations:
                - `prefs`: in format returned by ``dms2_prefs``
                - `mutdiffsel`: mutdiffsel from ``dms2_diffsel``
                - `abs_diffsel`: sitediffsel from ``dms2_diffsel``
                - `positive_diffsel`: sitediffsel from ``dms2_diffsel``
                - `max_diffsel`: sitediffsel from ``dms2_diffsel``
                - `mutfracsurvive`: from ``dms2_fracsurvive``
        `trim_unshared` (bool)
            What if files in `infiles` don't have same sites / mutations?
            If `True`, trim unshared one and just analyze ones
            shared among all files. If `False`, raise an error.
        `title` (str)
            Title to place above plot.
    """
    assert len(names) == len(infiles) == len(set(names)) > 1
    assert os.path.splitext(plotfile)[1].lower() == '.pdf'

    # corr coefficients as here: https://stackoverflow.com/a/30942817
    def corrfunc(x, y, **kws):
        r, _ = scipy.stats.pearsonr(x, y)
        ax = plt.gca()
        ax.annotate('R = {0:.2f}'.format(r), xy=(0.05, 0.9), 
                xycoords=ax.transAxes, fontsize=19, 
                fontstyle='oblique')

    if datatype == 'prefs':
        # read prefs into dataframe, ensuring all have same characters
        prefs = [pandas.read_csv(f).assign(name=name) for (name, f) 
                in zip(names, infiles)]
        chars = set(prefs[0].columns)
        sites = set(prefs[0]['site'].values)
        for p in prefs:
            unsharedchars = chars.symmetric_difference(set(p.columns))
            if unsharedchars:
                raise ValueError("infiles don't have same characters: {0}"
                        .format(unsharedchars))
            unsharedsites = sites.symmetric_difference(set(p['site']))
            if trim_unshared:
                sites -= unsharedsites
            elif unsharedsites:
                raise ValueError("infiles don't have same sites: {0}".
                        format(unsharedsites))
        assert {'site', 'name'} < chars
        chars = list(chars - {'site', 'name'})
        # get measurements for each replicate in its own column
        df = (pandas.concat(prefs, ignore_index=True)
                    .query('site in @sites') # only keep shared sites
                    .melt(id_vars=['name', 'site'], var_name='char')
                    .pivot_table(index=['site', 'char'], columns='name')
                    )
        df.columns = df.columns.get_level_values(1)

    elif datatype in ['mutdiffsel', 'mutfracsurvive']:
        mut_df = [pandas.read_csv(f)
                        .assign(name=name)
                        .assign(mutname=lambda x: x.wildtype +
                                x.site.map(str) + x.mutation)
                        .sort_values('mutname')
                        [['name', 'mutname', datatype]]
                    for (name, f) in zip(names, infiles)]
        muts = set(mut_df[0]['mutname'].values)
        for m in mut_df:
            unsharedmuts = muts.symmetric_difference(set(m['mutname']))
            if trim_unshared:
                muts -= unsharedmuts
            elif unsharedmuts:
                raise ValueError("infiles don't have same muts: {0}".
                        format(unsharedmuts))
        df = (pandas.concat(mut_df, ignore_index=True)
                    .query('mutname in @muts') # only keep shared muts
                    .pivot_table(index='mutname', columns='name')
                    .dropna()
                    )
        df.columns = df.columns.get_level_values(1)

    elif datatype in ['abs_diffsel', 'positive_diffsel', 'max_diffsel',
            'avgfracsurvive', 'maxfracsurvive']:
        site_df = [pandas.read_csv(f)
                         .assign(name=name)
                         .sort_values('site')
                         [['name', 'site', datatype]]
                    for (name, f) in zip(names, infiles)]
        sites = set(site_df[0]['site'].values)
        for s in site_df:
            unsharedsites = sites.symmetric_difference(set(s['site']))
            if trim_unshared:
                sites -= unsharedsites
            elif unsharedsites:
                raise ValueError("infiles don't have same sites: {0}".
                        format(unsharedsites))
        df = (pandas.concat(site_df, ignore_index=True)
                    .query('site in @sites') # only keep shared sites
                    .pivot_table(index='site', columns='name')
                    .dropna()
                    )
        df.columns = df.columns.get_level_values(1)

    else:
        raise ValueError("Invalid datatype {0}".format(datatype))

    # map lower / upper / diagonal as here:
    # https://stackoverflow.com/a/30942817 for plot
    p = seaborn.PairGrid(df)
    p.map_lower(plt.scatter, s=22, alpha=0.35, color='black', 
            marker='o', edgecolor='none', rasterized=True)
    p.map_lower(corrfunc)
    if datatype == 'prefs':
        p.set(  xlim=(0, 1), 
                ylim=(0, 1), 
                xticks=[0, 0.5, 1],
                yticks=[0, 0.5, 1],
                xticklabels=['0', '0.5', '1'],
                yticklabels=['0', '0.5', '1'],
                )
        # hide upper, diag: https://stackoverflow.com/a/34091733
        for (i, j) in zip(*numpy.triu_indices_from(p.axes, 1)):
            p.axes[i, j].set_visible(False)
        for (i, j) in zip(*numpy.diag_indices_from(p.axes)):
            p.axes[i, j].set_visible(False)

    elif datatype in ['mutdiffsel', 'abs_diffsel', 'positive_diffsel',
            'max_diffsel', 'mutfracsurvive', 'avgfracsurvive',
            'maxfracsurvive']:

        p.map_diag(seaborn.distplot, color='black', kde=True, hist=False)

        (lowlim, highlim) = (df.values.min(), df.values.max())
        highlim += (highlim - lowlim) * 0.05
        lowlim -= (highlim - lowlim) * 0.05
        p.set(xlim=(lowlim, highlim), ylim=(lowlim, highlim))

        # hide upper
        for (i, j) in zip(*numpy.triu_indices_from(p.axes, 1)):
            p.axes[i, j].set_visible(False)

    else:
        raise ValueError("invalid datatype")
        p.map_upper(seaborn.kdeplot, n_levels=20, cmap='Blues_d')

    if title:
        # following here: https://stackoverflow.com/a/29814281
        p.fig.suptitle(title)

    p.savefig(plotfile)
    plt.close()


def plotSiteDiffSel(names, diffselfiles, plotfile, 
        diffseltype, maxcol=2):
    """Plot site diffsel or fracsurvive along sequence.

    Despite the function name, this function can be used to
    plot either differential selection or fraction surviving.

    Args:
        `names` (list or series)
            Names of samples for which we plot statistics.
        `diffselfiles` (list or series)
            ``*sitediffsel.csv`` files from ``dms2_diffsel`` or
            ``*sitefracsurvive.csv`` files from ``dms2_fracsurvive``.
        `plotfile` (str)
            Name of created PDF plot file.
        `diffseltype` (str)
            Type of diffsel or fracsurvive to plot:
                - `positive`: positive sitediffsel
                - `total`: positive and negative sitediffsel
                - `max`: maximum mutdiffsel
                - `minmax`: minimum and maximum mutdiffsel
                - `avgfracsurvive`: total site fracsurvive
                - `maxfracsurvive`: max mutfracsurvive at site
        `maxcol` (int)
            Number of columns in faceted plot.
    """
    assert len(names) == len(diffselfiles) == len(set(names)) > 0
    assert os.path.splitext(plotfile)[1].lower() == '.pdf'

    diffsels = [pandas.read_csv(f).assign(name=name) for (name, f) 
            in zip(names, diffselfiles)]
    assert all([set(diffsels[0]['site']) == set(df['site']) for df in 
            diffsels]), "diffselfiles not all for same sites"
    diffsel = pandas.concat(diffsels, ignore_index=True)

    ylabel = 'differential selection'
    if diffseltype == 'positive':
        rename = {'positive_diffsel':'above'}
    elif diffseltype == 'total':
        rename = {'positive_diffsel':'above',
                  'negative_diffsel':'below'}
    elif diffseltype == 'max':
        rename = {'max_diffsel':'above'}
    elif diffseltype == 'minmax':
        rename = {'max_diffsel':'above',
                  'min_diffsel':'below'}
    elif diffseltype in ['avgfracsurvive', 'maxfracsurvive']:
        ylabel = 'fraction surviving'
        rename = {diffseltype:'above'}
    else:
        raise ValueError("invalid diffseltype {0}".format(diffseltype))
    diffsel = (diffsel.rename(columns=rename)
                      .melt(id_vars=['site', 'name'], 
                            value_vars=list(rename.values()),
                            value_name='diffsel',
                            var_name='direction')
                      )
    # natural sort by site: https://stackoverflow.com/a/29582718
    diffsel = diffsel.reindex(index=natsort.order_by_index(
            diffsel.index, natsort.index_natsorted(diffsel.site,
            signed=True)))
    # now some manipulations to make site str while siteindex is int
    diffsel['site'] = diffsel['site'].apply(str)
    diffsel['siteindex'] = pandas.Categorical(diffsel['site'],
            diffsel['site'].unique()).codes
    
    ncol = min(maxcol, len(names))
    nrow = math.ceil(len(names) / float(ncol))

    # make name a category to preserve order
    diffsel['name'] = diffsel['name'].astype('category', 
            categories=names)

    (xbreaks, xlabels) = breaksAndLabels(diffsel['siteindex'].unique(), 
            diffsel['site'].unique(), n=6)
    p = (ggplot(diffsel, aes(x='siteindex', y='diffsel', color='direction'))
            + geom_step(size=0.4)
            + xlab('site')
            + ylab(ylabel)
            + scale_x_continuous(breaks=xbreaks, labels=xlabels)
            + scale_color_manual(COLOR_BLIND_PALETTE)
            + guides(color=False)
            )
    if not ((len(names) == 1) and ((not names[0]) or names[0].isspace())):
        p += facet_wrap('~name', ncol=ncol)
    p += theme(figure_size=(4.6 * (0.3 + ncol), 1.9 * (0.2 + nrow)))
    p.save(plotfile, verbose=False)
    plt.close()



if __name__ == '__main__':
    import doctest
    doctest.testmod()
