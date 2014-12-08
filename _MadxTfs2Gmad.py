import numpy as _np
import pymadx
import Builder


def MadxTfs2Gmad(input,outputfilename,startname=None,endname=None,ignorezerolengthitems=True,samplers='all',aperturedict={},collimatordict={},beampipeRadius=0.2,verbose=False,):
    """
    MadxTfs2Gmad - convert a madx twiss output file (.tfs) into a gmad input file for bdsim

    MadxTfs2Gamd(inputfilename,
                 outputfilename,
                 startname             = None,
                 endname               = None,
                 ignorezerolengthitems = True,
                 samplers              = 'all',
                 aperturedict          = {},
                 collimatordict        = {}, 
                 beampipeRaidius       = 0.2, 
                 verbose               = False
                 )

    inputfilename  - path to the input file
    outputfilename - requested output file
    startname      - the name (exact string match) of the lattice element to start the machine at
                     this can also be an integer index of the element sequence number in madx tfs
    stopname       - the name (exact string match) of the lattice element to stop the machine at
                     this can also be an integer index of the element sequence number in madx tfs

    ignorezerolengthitems = True - nothing can be zero length in bdsim as real objects 
                                   of course have some finite size.  Markers, etc are 
                                   acceptable but for large lattices this can slow things down.
                                   True allows to ignore these altogether, which doesn't
                                   affect the length of the machine.

    samplers   - can specify where to set samplers - options are None, 'all', or list of 
                 names of elements (normal python list of strings). Note default 'all' 
                 will generate separate outputfilename_samplers.gmad with all the samplers
                 which will be included in the main .gmad file - you can comment out the 
                 include to therefore exclude all samplers and retain the samplers file.

    aperturedict - a dictionary of aperture information.  
                   keys should be exact string match of element name in tfs file
                   value should be a single number of the circular aperture (only circular just now)
                   e.g.  aperturdict = {'TCT1Bxy2':0.15,'TCT2Bxy2:0.20}
                   note values in metres

    collimatordict - a dictionary of dictionaries with collimator information
                     keys should be exact string match of element name in tfs file
                     value should be dictionary with the following keys:
                     "bdsim_material"   - the material - exact string as in bdsim manual
                     "angle"            - rotation angle of collimator in radians
                     "xsize"            - x full width in metres
                     "ysize"            - y full width in metres

    beampipeRadius - in metres.  Default beam pipe radius and collimator setting if unspecified

    verbose - print out lots of information when building the model

    """
    izlis  = ignorezerolengthitems
    if type(input) == 'str' :  
        madx   = pymadx.Tfs(inputfilename)
    else : 
        madx   = input

    nitems = madx.nitems
    opencollimatorsetting = beampipeRadius

    if verbose:
        madx.ReportPopulations()
        aper.ReportPopulations()

    # data structures for checks
    angtot = 0.0
    lentot = 0.0
    lldiff = []
    dldiff = {}
    itemsomitted = []

    kws = {} #extra parameters TO BE FINISHED
    
    #iterate through items in tfs and construct machine
    a = Builder.Machine()
    
    #prepare index for iteration:
    if startname == None:
        startindex = 0
    elif type(startname) == int:
        startindex = startname
    else:
        startindex = _IndexOfElement(madx,startname)
    if endname   == None:
        stopindex = nitems #this is 1 larger, but ok as range will stop at n-step -> step=1, range function issue
    elif type(stopname) == int:
        stopindex = stopname
    else:
        stopindex  = _IndexOfElement(madx,endname)
    if stopindex <= startindex:
        print 'stopindex <= startindex'
        stopindex = startindex + 1

    lindex     = madx.ColumnIndex('L')
    angleindex = madx.ColumnIndex('ANGLE')
    k1lindex   = madx.ColumnIndex('K1L')
    k2lindex   = madx.ColumnIndex('K2L')
    k3lindex   = madx.ColumnIndex('K3L')
    tindex     = madx.ColumnIndex('KEYWORD')
    if verbose:
        print 'L       Column Index: ',lindex
        print 'ANGLE   Column Index: ',angleindex
        print 'K1L     Column Index: ',k1lindex
        print 'K2L     Column Index: ',k2lindex
        print 'K3L     Column Index: ',k3lindex
        print 'KEYWORD Column Index: ',tindex
     
    # iterate through input file and construct machine
    for i in range(startindex,stopindex):
        name = madx.sequence[i]
        #remove special characters like $, % etc 'reduced' name - rname
        rname = ''.join(e for e in name if e.isalnum()) 
        t     = madx.data[name][tindex]
        l     = madx.data[name][lindex]
        ang   = madx.data[name][angleindex]
        if l <1e-9:
            zerolength = True
        else:
            zerolength = False
        if verbose:
            print 'zerolength? ',str(name).ljust(20),str(l).ljust(20),' ->',zerolength
        lentot += l
        angtot += ang

        #element-wise keywords
        kws = {}
        if name in aperturedict:
            #for now only 1 aperture - circular
            ap = (aperturedict[name],'m')
            if ap[0] < 1e-4:
                ap = (defaultbeampiperadius,'m')
            if t != 'RCOLLIMATOR':
                kws['aper'] = ap

        #if l == 0 and izlis == True:
        #    pass
        if t == 'DRIFT':
            a.AddDrift(rname,l,**kws)
        elif t == 'HKICKER':
            a.AddHKicker(rname,l,**kws)
        elif t == 'INSTRUMENT':
            #most 'instruments' are just markers
            if izlis and zerolength:
                itemsomitted.append(name)
            elif (not izlis) and zerolength:
                a.AddMarker(rname)
                if verbose:
                    print name,' -> marker instead of instrument'
            else:
                a.AddDrift(rname,l,**kws)
        elif t == 'MARKER':
            if izlis:
                itemsomitted.append(name)
            else:
                a.AddMarker(rname)
        elif t == 'MONITOR':
            #most monitors are just markers
            if izlis and zerolength:
                itemsomitted.append(name)
            elif (not izlis) and zerolength:
                a.AddMarker(rname)
                if verbose:
                    print name,' -> marker instead of monitor'
            else:
                a.AddDrift(rname,l,**kws)
        elif t == 'MULTIPOLE':
            #figure out which components are non zero
            #a.AddMultipole(name,l,)
            #TO BE FINISHED
            if izlis and zerolength:
                itemsomitted.append(name)
            elif (not izlis) and zerolength:
                a.AddMarker(rname)
                if verbose:
                    print name,' -> marker instead of multipole'
            else:
                a.AddDrift(rname,l,**kws)
        elif t == 'OCTUPOLE':
            #TO BE FINISHED
            if izlis and zerolength:
                itemsomitted.append(name)
            elif (not izlis) and zerolength:
                a.AddMarker(rname)
                if verbose:
                    print name,' -> marker instead of octupole'
            else:
                #NO implmentation of octupoles yet..
                a.AddDrift(rname,l,**kws)
        elif t == 'PLACEHOLDER':
            if izlis and zerolength:
                itemsomitted.append(name)
            elif (not izlis) and zerolength:
                a.AddMarker(rname)
            else:
                a.AddDrift(rname,l,**kws)
                if verbose:
                    print name,' -> marker instead of placeholder'
        elif t == 'QUADRUPOLE':
            k1 = madx.data[name][k1lindex] / l
            a.AddQuadrupole(rname,l,k1=k1,**kws)
        elif t == 'RBEND':
            angle = madx.data[name][angleindex]
            a.AddDipole(rname,'rbend',l,angle=angle,**kws)
        elif t == 'RCOLLIMATOR':
            #only use xsize as only have half gap
            if name in collimatordict:
                if 'bdsim_material' in collimatordict[name]:
                    kws['material'] = collimatordict[name]['bdsim_material']
                else:
                    kws['material'] = 'Copper'
                if 'xsize' in collimatordict[name]:
                    xsize = collimatordict[name]['xsize']
                else:
                    xsize = opencollimatorsetting
                if 'ysize' in collimatordict[name]:
                    ysize = collimatordict[name]['ysize']
                else:
                    tsize = opencollimatorsetting
                if 'angle' in collimatordict[name]:
                    angle = collimatordict[name]['angle']
                else:
                    angle = 0.0
            else:
                xsize = beampipeRadius
                ysize = beampipeRadius
                angle = 0.0
                kws['material'] = "Copper"
            a.AddRColAngled(rname,l,xsize,ysize,angle,**kws)
        elif t == 'ECOLLIMATOR':
            if name in collimatordict:
                if 'bdsim_material' in collimatordict[name]:
                    kws['material'] = collimatordict[name]['bdsim_material']
                else:
                    kws['material'] = 'Copper'
                if 'xsize' in collimatordict[name]:
                    xsize = collimatordict[name]['xsize']
                else:
                    xsize = opencollimatorsetting
                if 'ysize' in collimatordict[name]:
                    ysize = collimatordict[name]['ysize']
                else:
                    tsize = opencollimatorsetting
                if 'angle' in collimatordict[name]:
                    angle = collimatordict[name]['angle']
                else:
                    angle = 0.0
            else:
                xsize = beampipeRadius
                ysize = beampipeRadius
                angle = 0.0
                kws['material'] = "Copper"
            a.AddEColAngled(rname,l,xsize,ysize,angle,**kws)
        elif t == 'RFCAVITY':
            a.AddDrift(rname,l,**kws)
        elif t == 'SBEND':
            angle = madx.data[name][angleindex]
            a.AddDipole(rname,'sbend',l,angle=angle,**kws)
        elif t == 'SEXTUPOLE':
            k2 = madx.data[name][k2lindex] / l
            a.AddSextupole(rname,l,k2=k2,**kws)
        elif t == 'SOLENOID':
            a.AddDrift(rname,l,**kws)
        elif t == 'TKICKER':
            a.AddDrift(rname,l,**kws)
        elif t == 'VKICKER':
            a.AddDrift(rname,l,**kws)
        else:
            print 'unknown element type: ',t,' for element named: ',name
            if zerolength:
                if izlis :
                    itemsomitted.append(name)
                else:
                    print 'putting marker in instead as its zero length'
                    a.AddMarker(rname)
            else:
                print 'putting drift in instead as it has finite length'
                a.AddDrift(rname,l)

    #add a single marker at the end of the line
    a.AddMarker('theendoftheline')
    
    a.AddSampler(samplers)
    a.WriteLattice(outputfilename)

    if verbose:
        print 'lentot ',lentot
        print 'angtot ',angtot
        print 'items omitted: '
        print itemsomitted
        #return lldiff,dldiff,a
    return a