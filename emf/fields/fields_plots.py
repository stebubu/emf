import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
lines = mpl.lines

from ..emf_plots import _save_fig

import fields_funks

#rcparams for more static global formatting changes
mpl.rcParams['figure.facecolor'] = 'white'
mpl.rcParams['figure.figsize'] = (12, 6)
mpl.rcParams['font.family'] = 'Times New Roman'
mpl.rcParams['text.color'] = (.2, .2, .2)
mpl.rcParams['axes.labelcolor'] = (.2, .2, .2)
mpl.rcParams['axes.titlesize'] = 16
mpl.rcParams['axes.labelsize'] = 14
mpl.rcParams['legend.fontsize'] = 10
mpl.rcParams['legend.borderaxespad'] = 0 #mpl default is None
mpl.rcParams['xtick.color'] = (.2, .2, .2)
mpl.rcParams['ytick.color'] = (.2, .2, .2)

#other more specific/dynamic global formatting variables
_B_color = 'darkgreen'
_E_color = 'midnightblue'
_fields_linewidth = 2
_ROW_linewidth = 0.75
_ROW_color = 'gray'
_ax_frameon = False
_ax_ticks_on = False
_leg_edge_on = False
_colormap = [(0, 0.4470, 0.7410),(0.8500, 0.3250,0.0980),
            (0.9290, 0.6940, 0.1250),(0.4940, 0.1840, 0.5560),
            (0.4660, 0.6740, 0.1880),(0.3010, 0.7450, 0.9330),
            (0.6350, 0.0780, 0.1840)]

#-------------------------------------------------------------------------------
#general plotting support functions

def ion():
    plt.ion()

def show():
    plt.show()

def close(*args):
    if(args):
        for a in args:
            if(hasattr(a, '__len__')):
                for b in a:
                    plt.close(b.number)
            else:
                plt.close(a.number)
    else:
        plt.close('all')

def _format_axes_legends(*args):
    """Apply axis formatting commands to axes objects
    args: some number of axis objects with twin x axes"""
    for ax in args:
        #apply legend formatting
        leg = ax.get_legend()
        if(leg):
            rec = leg.get_frame()
            if(not _leg_edge_on):
                rec.set_edgecolor('white')
        #apply axis formatting
        ax.set_frame_on(_ax_frameon)
        if(not _ax_ticks_on):
            ax.tick_params(axis = 'both', which = 'both',
                bottom = 'off', top = 'off', left = 'off', right = 'off')
    #take care of scaling problems caused by underground lines
    if(len(args) > 1):
        #get minimum y limit
        ylow, yhigh = 0., 0.
        for ax in args:
            yl = ax.get_ylim()
            if(yl[0] < ylow):
                ylow = yl[0]
                yhigh = yl[1]
        #scale all axes identically so that they overlap at y = 0
        if(ylow != 0.):
            frac = ylow/yhigh
            for ax in args:
                yl = ax.get_ylim()
                ax.set_ylim(frac*yl[1], yl[1])

def _color_twin_axes(ax1, color1, ax2, color2):
    """Assign colors to split y axes"""
    #spines
    ax1.spines['left'].set_color(color1)
    ax1.spines['right'].set_color(color2)
    ax2.spines['left'].set_color(color1)
    ax2.spines['right'].set_color(color2)
    #text
    ax1.yaxis.label.set_color(color1)
    ax2.yaxis.label.set_color(color2)
    #ticks
    ax1.tick_params(axis = 'y', colors = color1)
    ax2.tick_params(axis = 'y', colors = color2)

#-------------------------------------------------------------------------------
#plotting routines working with a CrossSection object

#useful globals for the CrossSection plotting routines, unlikely to collide
#with other variables of the same name
_fields_plots_xc_headspace = 0.4 #space at the top of plots for legend
_fields_plots_xc_wireperc = 0.3 #percent of max field value to scale wire heights

def _prepare_fig(xc, **kwargs):
    """Snippet executed at the beginning of plotting methods to handle figure
    object generation and some keywords initializing other params.
    args:
        xc - CrossSection objects
    kwargs:
        figure - figure object to recycle, if needed
        xmax - cutoff distance from the ROW center"""
    #prepare figure and axis
    if('figure' in kwargs):
        fig = kwargs['figure']
    else:
        fig = plt.figure()
    ax = plt.gca()
    #get x cutoff, if any
    if('xmax' in kwargs):
        xmax = abs(kwargs['xmax'])
    else:
        xmax = max(abs(xc.fields.index))
    #get appropriate linestyle based on number of sample points
    n = xc.fields[-xmax:xmax].shape[0]
    if(n > 100):
        linesym = '-'
    else:
        linesym = '.-'
    return(fig, ax, xmax, linesym)

def _plot_wires(ax, hot, gnd, v):
    """Plot conductor symbols in ax.Returns handles for the hot and gnd
    Conductors.
    args:
        ax - target axis
        hot - list of non-grounded conductors
        gnd - list of grounded conductors
        v - iterable of calculated field results used to scale conductors"""
    #get x and y coordinates
    x = np.array([c.x for c in hot + gnd])
    y = np.array([c.y for c in hot + gnd])
    #calculate the scaling factor
    scale = _fields_plots_xc_wireperc*np.max(v)/np.max(np.absolute(y))
    #plot
    h, l = [], []
    if(hot):
        h.append(ax.plot(x[:len(hot)], scale*y[:len(hot)], 'kd')[0])
        l.append('Conductors')
    if(gnd):
        h.append(ax.plot(x[len(hot):], scale*y[len(hot):], 'd', color = 'gray')[0])
        l.append('Grounded Conductors')
    return(h, l)

def _plot_ROW_edges(ax, lROW, rROW):
    """Plot dashed lines marking the left and right edges of the
    Right-of-Way. Axis limits are also adjusted to allow extra space on the
    sides to make the ROW edge lines visible if needed. The ROW edge line
    handles are returned in a list.
    args:
        ax - target axis
        lROW - x value of the left edge of the ROW
        rROW - x value of the right edge of the ROW"""
    yl = ax.get_ylim()
    hROW = ax.plot([lROW]*2, yl, '--', color = _ROW_color,
                        linewidth = _ROW_linewidth, zorder = -1)
    ax.plot([rROW]*2, yl, '--', color = _ROW_color,
                linewidth = _ROW_linewidth, zorder = -1)
    l = ['ROW Edges']
    xl = ax.get_xlim()
    if((xl[0] == lROW) or (xl[1] == rROW)):
        ax.set_xlim((xl[0]*1.15, xl[1]*1.15))
    return(hROW, l)

def plot_Bmax(xc, **kwargs):
    """Plot the maximum magnetic field along the ROW with conductor
    locations shown in artificial coordinates.
    args:
        xc - a CrossSection object
    kwargs:
        figure - matplotlib Figure object, target figure for plotting
        title - string, exact plot title
        save - bool, toggle plot saving
        path - string, destination/filename for saved figure
        format - string, saved plot format/extension (default 'png')
    returns:
        fig - Figure object"""
    #get axes and x cutoff
    (fig, ax, xmax, linesym) = _prepare_fig(xc, **kwargs)
    #plot the field curve
    hB = ax.plot(xc.fields['Bmax'][-xmax:xmax], linesym,
                color = _B_color,
                linewidth = _fields_linewidth)
    lB = [r'Magnetic Field $\left(mG\right)$']
    #plot wires
    hw, lw = _plot_wires(ax, xc.hot, xc.gnd, xc.fields['Bmax'])
    #adjust axis limits
    #ax.set_ylim(0, (1 + _fields_plots_xc_headspace)*max(xc.fields['Bmax']))
    #plot ROW lines
    hROW, lROW = _plot_ROW_edges(ax, xc.lROW, xc.rROW)
    #set axis text and legend
    ax.set_xlabel('Distance from Center of ROW (ft)')
    ax.set_ylabel(r'Maximum Magnetic Field $\left(mG\right)$')
    if('title' in kwargs):
        t = kwargs['title']
    else:
        t = 'Maximum Magnetic Field - %s' % xc.subtitle
    ax.set_title(t)
    ax.legend(hB + hw + hROW, lB + lw + lROW, numpoints = 1)
    _format_axes_legends(ax)
    #save the fig or don't, depending on keywords
    _save_fig(xc.name, fig, **kwargs)
    #return
    return(fig)

def plot_Emax(xc, **kwargs):
    """Plot the maximum electric field along the ROW with conductor
    locations shown in artificial coordinates.
    args:
        xc - a CrossSection object
    kwargs:
        figure - matplotlib Figure object, target figure for plotting
        title - string, exact plot title
        save - bool, toggle plot saving
        path - string, destination/filename for saved figure
        format - string, saved plot format/extension (default 'png')
    returns:
        fig - Figure object"""
    #get axes and x cutoff
    (fig, ax, xmax, linesym) = _prepare_fig(xc, **kwargs)
    #plot the field curve
    hE = ax.plot(xc.fields['Emax'][-xmax:xmax], linesym,
                color = _E_color,
                linewidth = _fields_linewidth)
    lE = [r'Electric Field $\left(kV/m\right)$']
    #plot wires
    hw, lw = _plot_wires(ax, xc.hot, xc.gnd, xc.fields['Emax'])
    #plot ROW lines
    hROW, lROW = _plot_ROW_edges(ax, xc.lROW, xc.rROW)
    #set axis text and legend
    ax.set_xlabel('Distance from Center of ROW (ft)')
    ax.set_ylabel(r'Maximum Electric Field $\left(kV/m\right)$')
    if('title' in kwargs):
        t = kwargs['title']
    else:
        t = 'Maximum Electric Field - %s' % xc.subtitle
    ax.set_title(t)
    ax.legend(hE + hw + hROW, lE + lw + lROW, numpoints = 1)
    _format_axes_legends(ax)
    #save the fig or don't, depending on keywords
    _save_fig(xc.name, fig, **kwargs)
    #return
    return(fig)

def plot_max_fields(xc, **kwargs):
    """Plot the maximum magnetic and electric field on split vertical axes,
    along the ROW with conductor locations shown in artificial coordinates.
    args:
        xc - a CrossSection object
    kwargs:
        figure - matplotlib Figure object, target figure for plotting
        title - string, exact plot title
        save - bool, toggle plot saving
        path - string, destination/filename for saved figure
        format - string, saved plot format/extension (default 'png')
    returns:
        fig - Figure object"""
    #get axes and x cutoff
    (fig, ax_B, xmax, linesym) = _prepare_fig(xc, **kwargs)
    ax_E = ax_B.twinx()
    #plot the field curves
    hf = [ax_B.plot(xc.fields['Bmax'][-xmax:xmax], linesym,
                color = _B_color,
                linewidth = _fields_linewidth)[0],
            ax_E.plot(xc.fields['Emax'][-xmax:xmax], linesym,
                color = _E_color,
                linewidth = _fields_linewidth)[0]]
    lf = [r'Magnetic Field $\left(mG\right)$',
            r'Electric Field $\left(kV/m\right)$']
    #plot wires
    hw, lw = _plot_wires(ax_B, xc.hot, xc.gnd, xc.fields['Bmax'])
    #plot ROW lines
    hROW, lROW = _plot_ROW_edges(ax_B, xc.lROW, xc.rROW)
    #set axis text
    ax_B.set_xlabel('Distance from Center of ROW (ft)')
    ax_B.set_ylabel(r'Maximum Magnetic Field $\left(mG\right)$',
            color = _B_color)
    ax_E.set_ylabel(r'Maximum Electric Field $\left(kV/m\right)$',
            color = _E_color)
    if('title' in kwargs):
        t = kwargs['title']
    else:
        t = 'Maximum Magnetic and Electric Fields - %s' % xc.subtitle
    ax_B.set_title(t)
    #set color of axis spines and ticklabels
    _color_twin_axes(ax_B, _B_color, ax_E, _E_color)
    #legend
    ax_B.legend(hf + hw + hROW, lf + lw + lROW, numpoints = 1)
    _format_axes_legends(ax_B, ax_E)
    #save the fig or don't, depending on keywords
    _save_fig(xc.name, fig, **kwargs)
    #return
    return(fig)

def _plot_DAT_repeatables(ax_abs, ax_per, ax_mag, pan, field, hw, lw):
    """Handle plotting of DAT comparison features that don't require unique
    strings
    args:
        ax_abs - axis of absolute error plot
        ax_per - axis of percentage error plot
        ax_mag - axis of field magnitude plot
        pan - pandas.Panel object containing results and errors
        field - string, column label of field to be plotted (Bmax/Emax)
        hw - handles of the conductor symbol plots
        lw - labels for conductor symbols"""
    #plot absolute error
    h_abs = ax_abs.plot(pan['Absolute Difference'][field], 'k')
    ax_abs.set_ylabel(r'Absolute Difference $\left(kV/m\right)$')
    #plot percentage error
    h_per = ax_per.plot(pan['Percent Difference'][field], 'r')
    ax_per.set_ylabel('Percent Difference', color = 'r')
    #set error axes legend
    ax_abs.legend(h_abs + h_per, ['Absolute Difference','Percent Difference'])
    #plot results
    h_fld = ax_mag.plot(pan['FIELDS_DAT_results'][field], 'k')
    h_nm = ax_mag.plot(pan['python_results'][field], 'b')
    ax_mag.set_xlabel('Distance from ROW Center (ft)')
    #set results legend
    ax_mag.legend(h_fld + h_nm + hw, ['FIELDS','New Code'] + lw, numpoints = 1)

def plot_DAT_comparison(xc, pan, **kwargs):
    """Generate 2 subplots showing the FIELDS results (from a .DAT file)
    compared to the results of this code and the error.
    args:
        xc - CrossSection object
        pan - pandas.Panel object containing results and errors
    kwargs:
        save - bool, toggle plot saving
        path - string, destination/filename for saved figure
        format - string, saved plot format/extension (default 'png')"""

    #figure object and axes
    fig = plt.figure()
    ax_abs = fig.add_subplot(2,1,1)
    ax_per = ax_abs.twinx()
    ax_mag = fig.add_subplot(2,1,2)
    #Bmax
    hw, lw = _plot_wires(ax_mag, xc.hot, xc.gnd, pan['python_results']['Bmax'])
    _plot_DAT_repeatables(ax_abs, ax_per, ax_mag, pan, 'Bmax', hw, lw)
    ax_abs.set_title('Absolute and Percent Difference, Max Magnetic Field')
    ax_mag.set_ylabel(r'Bmax $\left(mG\right)$')
    ax_mag.set_title('Model Results, Magnetic Field')
    _color_twin_axes(ax_abs, mpl.rcParams['axes.labelcolor'], ax_per, 'r')
    _format_axes_legends(ax_abs)
    plt.tight_layout()
    #_format_axes_legends(ax_abs, ax_per, ax_mag)
    _save_fig(xc.name + '-DAT_comparison_Bmax', fig, **kwargs)
    plt.close(fig)

    #figure object and axes
    fig = plt.figure()
    ax_abs = fig.add_subplot(2,1,1)
    ax_per = ax_abs.twinx()
    ax_mag = fig.add_subplot(2,1,2)
    #Emax
    hw, lw = _plot_wires(ax_mag, xc.hot, xc.gnd, pan['python_results']['Emax'])
    _plot_DAT_repeatables(ax_abs, ax_per, ax_mag, pan, 'Emax', hw, lw)
    ax_abs.set_title('Absolute and Percent Difference, Max Electric Field')
    ax_mag.set_ylabel(r'Emax $\left(kV/m\right)$')
    ax_mag.set_title('Model Results, Electric Field')
    _color_twin_axes(ax_abs, mpl.rcParams['axes.labelcolor'], ax_per, 'r')
    plt.tight_layout()
    #_format_axes_legends(ax_abs, ax_per, ax_mag)
    _save_fig(xc.name + '-DAT_comparison_Emax', fig, **kwargs)
    plt.close(fig)


#-------------------------------------------------------------------------------
#plotting routines working primarily with a SectionBook object

#useful globals for the section book plotting routine(s), unlikely to collide
#with other variables of the same name
_fields_plots_sb_headspace = 0.4 #space at the top of plots for legend
_fields_plots_sb_wireperc = 0.3 #percent of max field value to scale wire heights

def _plot_group_fields(ax, xcs, field, **kwargs):
    """Plot the results of fields calculations
    args:
        ax - target axis
        xcs - list of CrossSection objects to plot results from
        field - column label of the results to plot
    kwargs:
        xmax - cutoff distance from ROW center"""
    #check for an xmax keyword
    if('xmax' in kwargs):
        xmax = kwargs['xmax']
    else:
        xmax = False
    #plot the fields, keeping handles and finding max of all
    fields_list = [xc.fields[field] for xc in xcs]
    h = []
    l = []
    max_field = 0.
    for i in range(len(fields_list)):
        #plot
        if(xmax):
            h.append(ax.plot(fields_list[i][-xmax:xmax],
                        color = _colormap[i%7],
                        linewidth = _fields_linewidth)[0])
        else:
            h.append(ax.plot(fields_list[i], color = _colormap[i%7],
                        linewidth = _fields_linewidth)[0])
        l.append(field + ' - ' + xcs[i].title)
        #find max
        if(max(fields_list[i]) > max_field):
            max_field = max(fields_list[i])
    return(h, l, max_field)

def _plot_group_wires(ax, xcs, max_field):
    """Plot the conductors of 1 or 2 CrossSections, using split color
    for conductor locations shared by 2 CrossSections
    args:
        ax - target axis
        xcs - list of CrossSection objects to plot results from
        max_field - maximum value of all fields plotted in ax"""
    #conductor markers not available for more than 2 cross sections for now
    h, l = [], []
    if(len(xcs) == 2):
        #---only hot conductors are plotted
        #---use sets to group shared and unshared conductor locations
        #get x and y pairs of Conductors in each group
        xy_0 = [(c.x,c.y) for c in xcs[0].hot]
        xy_1 = [(c.x,c.y) for c in xcs[1].hot]
        #zero the y coordinate of any underground lines
        for i in range(len(xy_0)):
            if(xy_0[i][1] < 0):
                xy_0[i] = (xy_0[i][0], 0.0)
        for i in range(len(xy_1)):
            if(xy_1[i][1] < 0):
                xy_1[i] = (xy_1[i][0], 0.0)
        #grab all x and y coordinates while they're available
        all_x, all_y = zip(*(xy_0 + xy_1))
        all_y = np.array(all_y)
        all_x = np.array(all_x)
        #use sets to form the groups of Conductors
        xy_0 = set(xy_0)
        xy_1 = set(xy_1)
        #assemble shared x,y pairs
        shared = xy_0 & xy_1
        #remove shared pairs from xy_0 and xy_1
        xy_0 -= shared
        xy_1 -= shared
        #plot shared conductors
        h = []
        l = []
        scale = _fields_plots_xc_wireperc*max_field/np.max(np.absolute(all_y))
        #cross section 0 conductors only
        if(len(xy_0) > 0):
            x,y = zip(*xy_0)
            h.append(ax.plot(x, scale*np.array(y), 'd',
                            color = _colormap[0])[0])
        else:
            #still need a handle for the legend
            h.append(lines.Line2D([], [], marker = 'd', linestyle = '',
                            color = _colormap[0]))
        l.append('Conductors - ' + xcs[0].title)
        #cross section 1 conductors only
        if(len(xy_1) > 0):
            x,y = zip(*xy_1)
            h.append(ax.plot(x, scale*np.array(y), 'd',
                            color = _colormap[1])[0])
        else:
            #still need a handle for the legend
            h.append(lines.Line2D([], [], marker = 'd', linestyle = '',
                            color = _colormap[1]))
        l.append('Conductors - ' + xcs[1].title)
        #shared conductors
        if(len(shared) > 0):
            x,y = zip(*shared)
            ax.plot(x, scale*np.array(y), 'd', color = _colormap[0],
                        fillstyle = 'left')
            ax.plot(x, scale*np.array(y), 'd', color = _colormap[1],
                        fillstyle = 'right')
    #return handles and labels
    return(h, l)

def _plot_group_ROW_edges(ax, xcs):
    """Plot lines delineating the Right-of-Way boundaries
    args:
        ax - target axis
        xcs - list of CrossSection objects to plot results from"""
    h, l = [], []
    #if there are only two CrossSections, handle ROW edges independently
    if(len(xcs) == 2):
        yl = ax.get_ylim()
        #check if the left ROW edges are in the same place for both sections
        if(xcs[0].lROW == xcs[1].lROW):
            #plot overlapping dashed lines to create double colored dashes
            ax.plot([xcs[0].lROW]*2, yl, '--', color = _colormap[0],
                        linewidth = _ROW_linewidth, zorder = -1,
                        dashes = [6,6,6,6])
            ax.plot([xcs[1].lROW]*2, yl, '--', color = _colormap[1],
                        linewidth = _ROW_linewidth, zorder = -1,
                        dashes = [6,18,6,18])
        else:
            ax.plot([xcs[0].lROW]*2, yl, '--', color = _colormap[0],
                        linewidth = _ROW_linewidth, zorder = -1)
            ax.plot([xcs[1].lROW]*2, yl, '--', color = _colormap[1],
                        linewidth = _ROW_linewidth, zorder = -1)
        #check if the left ROW edges are in the same place for both sections
        if(xcs[0].rROW == xcs[1].rROW):
            #plot overlapping dashed lines to create double colored dashes
            ax.plot([xcs[0].rROW]*2, yl, '--', color = _colormap[0],
                        linewidth = _ROW_linewidth, zorder = -1,
                        dashes = [6,6,6,6])
            ax.plot([xcs[1].rROW]*2, yl, '--', color = _colormap[1],
                        linewidth = _ROW_linewidth, zorder = -1,
                        dashes = [6,18,6,18])
        else:
            ax.plot([xcs[0].rROW]*2, yl, '--', color = _colormap[0],
                        linewidth = _ROW_linewidth, zorder = -1)
            ax.plot([xcs[1].rROW]*2, yl, '--', color = _colormap[1],
                        linewidth = _ROW_linewidth, zorder = -1)
        #create a line handle and label for each color of the dashed line
        h = [lines.Line2D([], [], linestyle = '--',color = _colormap[0]),
            lines.Line2D([], [], linestyle = '--', color = _colormap[1])]
        l = ['ROW Edges - ' + xcs[0].title, 'ROW Edges - ' + xcs[1].title]
    elif(len(xcs) > 2):
        #if there are more than two CrossSections and they all have the same
        #ROW edges, plot the single set of edge lines
        l, r = [xc.lROW for xc in xcs], [xc.rROW for xc in xcs]
        if(all([i == l[0] for i in l[1:]]) and all([i == r[0] for i in r[1:]])):
            h, l = _plot_ROW_edges(ax, l[0], r[0])
    return(h, l)


def plot_groups(sb, **kwargs):
    """Plot the fields of grouped CrossSections in the same axis, a plot for
    both fields. Only plots groups of more than one CrossSection.
    args:
        sb - SectionBook object to pull plotting groups from
    kwargs:
        save - bool, toggle plot saving
        path - string, destination/filename for saved figure
        format - string, saved plot format/extension (default 'png')
        xmax - cutoff distance from ROW center
        return_figs - toggle whether a list of figure objects is returned
                      instead of closing the figures to clear memory,
                      default is False
    returns:
        figs - list of figure objects created for each group, only returned
               if the kwarg 'return_figs' is True"""
    #check return kwarg
    return_figs = False
    if('return_figs' in kwargs):
        if(kwargs['return_figs']):
            return_figs = True
            figs = []
    #iterate over groups with more than 1 CrossSection
    for g in [group for group in sb.tag_groups if len(group) > 1]:
        xcs = [sb.xcs[i] for i in g]
        #BMAX
        #get plotting objects
        fig = plt.figure()
        ax = fig.add_subplot(1,1,1, frameon = _ax_frameon)
        #plot the Bmax results for each xc in the group
        h, l, max_field = _plot_group_fields(ax, xcs, 'Bmax', **kwargs)
        #plot wires
        hw, lw = _plot_group_wires(ax, xcs, max_field)
        #adjust axis limits
        #ax.set_ylim(0, (1 + _fields_plots_xc_headspace)*max_field)
        #plot ROW lines
        hROW, lROW = _plot_group_ROW_edges(ax, xcs)
        #set axis text and legend
        ax.set_xlabel('Distance from Center of ROW (ft)')
        ax.set_ylabel(r'Maximum Magnetic Field $\left(mG\right)$')
        t = 'Maximum Magnetic Field - Cross-Section Group %s' % str(xcs[0].tag)
        ax.set_title(t)
        ax.legend(h + hw + hROW, l + lw + lROW, numpoints = 1)
        _format_axes_legends(ax)
        #save the figure if keyword 'save' == True, and append fig to figs
        _save_fig('group_%s-Bmax' % str(xcs[0].tag), fig, **kwargs)
        #store the fig or close it
        if(return_figs):
            figs.append(fig)
        else:
            plt.close(fig)

        #EMAX
        #get plotting objects
        fig = plt.figure()
        ax = fig.add_subplot(1,1,1, frameon = _ax_frameon)
        #plot the Bmax results for each xc in the group
        h, l, max_field = _plot_group_fields(ax, xcs, 'Emax', **kwargs)
        #plot wires
        hw, lw = _plot_group_wires(ax, xcs, max_field)
        #adjust axis limits
        #ax.set_ylim(0, (1 + _fields_plots_xc_headspace)*max_field)
        #plot ROW lines
        hROW, lROW = _plot_group_ROW_edges(ax, xcs)
        #set axis text and legendf
        ax.set_xlabel('Distance from Center of ROW (ft)')
        ax.set_ylabel(r'Maximum Electric Field $\left(kV/m\right)$')
        t = 'Maximum Electric Field - Conductor Group %s' % str(xcs[0].tag)
        ax.set_title(t)
        ax.legend(h + hw + hROW, l + lw + lROW, numpoints = 1)
        _format_axes_legends(ax)

        #save the figure if keyword 'save' == True, and append fig to figs
        _save_fig('group_%s-Emax' % str(xcs[0].tag), fig, **kwargs)
        #store the fig or close it
        if(return_figs):
            figs.append(fig)
        else:
            plt.close(fig)
    if(return_figs):
        return(figs)