import pymadx.Ptc
import pymadx.Beam
import pymadx.Builder
import pymadx.Tfs
import pybdsim.Beam
import pybdsim.Builder
import pybdsim.Data
import pybdsim.Convert
import pybdsim.Testing
import pymadx as _pymadx
import os as _os
import matplotlib.pyplot as _plt
import robdsim
import numpy as _np
import root_numpy as _rnp


class FodoTest:
    def __init__(self,filename, nparticles = 1000, foldername=None):        
        """
        Takes a .madx file containing description of a lattice and generates
        BDSIM and MadX PTC jobs from it as well as MadX optical functions 
        propagation plots.

        nparticles - specifies the number of particles to be used for BDSIM/PTC runs
        """
        if filename[-5:] == ".madx":                
            self.filename    = filename[:-5]
            self.tfsfilename = str.lower(self.filename)
            self.foldername  = foldername
            self.ptcinrays   = self.filename+"_inrays.madx"
            self.ptcfilename = "ptc_"+self.filename+".madx"
            self.nparticles  = nparticles
            if self.foldername != None:
                self.usingfolder = True
                self.filepath    = self.foldername+'/'+self.filename
                _os.system("mkdir -p " + self.foldername)
                self.filepath    = self.foldername+self.filename+".madx"
            else:
                self.usingfolder = False
                self.filepath    = self.filename+".madx"
                self.figureNr    = 1729
        else:
            print "IOError: Not a valid file format!"   ###make this standard
            quit()

    def Clean(self):
        _os.system("rm -rf "+self.filename+"/")
        _os.system("rm -rf fodo*")
        _os.system("rm -rf *.log")
        _os.system("rm -rf *.dat")
        _os.system("rm -rf *.tfs")
        _os.system("rm -rf *.ps")
        _os.system("rm -rf ptc*")
        _os.system("rm -rf *.txt")
        _os.system("rm -rf *.root")
        _os.system("rm -rf *.gmad")
        _os.system("rm -rf *_inrays.madx")
        _os.system("rm -rf *.png")
        _os.system("rm -rf *.pdf")
        _os.system("rm trackone")

        # clean and close figures (9 figures in total)
        for i in range(10):
            _plt.close(self.figureNr+i)


    def Run(self):
        print 'Test> FODO:' 
        print 'Test> Destination filepath: ',self.filepath

        if self.usingfolder:
            _os.chdir(self.foldername)

        _os.system("madx-macosx64 < "+self.filename+".madx > madx.log")

        pybdsim.Convert.MadxTfs2Gmad(''+self.tfsfilename+'.tfs', self.filename) 
        _pymadx.MadxTfs2Ptc(''+self.tfsfilename+'.tfs', self.ptcfilename, self.ptcinrays)

        _os.system("bdsim --file="+self.filename+".gmad --ngenerate="+str(self.nparticles)+" --batch --output=root --outfile="+self.filename+" > bdsim.log")

        pybdsim.Testing.bdsimPrimaries2Ptc(''+self.filename+'.root', self.ptcinrays)

        _os.system("madx-macosx64 < "+self.ptcfilename+" > ptc_madx.log")
                
        if self.usingfolder:
            _os.chdir("../")


    def Compare(self, addPrimaries=True):
        """
        This function is adapted from trackingTester,in the future it will be
        further altered and upgraded to suit the needs of this tester
        """

        if self.usingfolder:
            _os.chdir(self.foldername)

        rootdata  = robdsim.robdsimOutput(self.filename+".root")

        primchain = rootdata.GetSamplerChain('primaries')
        bdsimprim = _rnp.tree2rec(primchain)
        Bx0 = bdsimprim['x']
        By0 = bdsimprim['y']
        Bxp0 = bdsimprim['xp']
        Byp0 = bdsimprim['yp']
        self.bdsimprimaries = {'x':Bx0,'y':By0,'xp':Bxp0,'yp':Byp0}

        endchain = rootdata.GetSamplerChain('Sampler_theendoftheline')
        bdsim = _rnp.tree2rec(endchain)
        Bx = bdsim['x']
        By = bdsim['y']
        Bxp = bdsim['xp']
        Byp = bdsim['yp']
        self.bdsimoutput = {'x':Bx,'y':By,'xp':Bxp,'yp':Byp}
        

        madx = pymadx.Tfs("trackone")
        madx = madx.GetSegment(madx.nsegments) #get the last 'segment' / sampler
        Mx = madx.GetColumn('X')*1e6 # convert from m to um
        My = madx.GetColumn('Y')*1e6 
        Mxp = madx.GetColumn('PX')
        Myp = madx.GetColumn('PY')
        self.ptcoutput = {'x':Mx,'y':My,'xp':Mxp,'yp':Myp}

        fresx  = _np.nan_to_num(Mx - Bx)
        fresy  = _np.nan_to_num(My - By)
        fresx  = _np.nan_to_num(fresx / Mx) #protect against nans for 0 diff
        fresy  = _np.nan_to_num(fresy / My)
        fresxp = _np.nan_to_num(Mxp - Bxp)
        fresyp = _np.nan_to_num(Myp - Byp)
        fresxp = _np.nan_to_num(fresxp / Mxp)
        fresyp = _np.nan_to_num(fresyp / Myp)
        self.residuals = {'x':fresx,'y':fresy,'xp':fresxp,'yp':fresyp}

        #standard deviation
        stdMx  = _np.std(Mx)
        stdMy  = _np.std(My)
        stdMxp = _np.std(Mxp)
        stdMyp = _np.std(Myp)

        stdBx  = _np.std(Bx)
        stdBy  = _np.std(By)
        stdBxp = _np.std(Bxp)
        stdByp = _np.std(Byp)

        frestdx  = _np.nan_to_num(stdMx - stdBx)
        frestdy  = _np.nan_to_num(stdMy - stdBy)
        frestdx  = _np.nan_to_num(frestdx / stdMx) #protect against nans for 0 diff
        frestdy  = _np.nan_to_num(frestdy / stdMy)
        frestdxp = _np.nan_to_num(stdMxp - stdBxp)
        frestdyp = _np.nan_to_num(stdMyp - stdByp)
        frestdxp = _np.nan_to_num(frestdxp / stdMxp)
        frestdyp = _np.nan_to_num(frestdyp / stdMyp)

        print 'stdFracErrX= ',frestdx,' stdFracErrY= ', frestdy, 'stdFracErrXP= ', frestdxp, 'stdFracErrX= ', frestdyp

        # write standard deviations to file
        with open(''+self.filename+'_stdev.txt', 'w') as stdout:
            h = self.filename+' stdev'
            h += '\t BDS_X \t MDX_x \t BDS_Y \t MDX_Y \t BDS_XP \t MDX_XP \t BDS_YP \t MDX_YP \t FRCERR_X \t FRCERR_Y \t FRCERR_XP \t FRCERR_YP\n'
            s  = '\t' +  str(stdBx)
            s += '\t' +  str(stdMx)
            s += '\t' +  str(stdBy)              
            s += '\t' +  str(stdMy)
            s += '\t' +  str(stdBxp)
            s += '\t' +  str(stdMxp)
            s += '\t' +  str(stdByp)
            s += '\t' +  str(stdMyp)
            s += '\t' +  str(frestdx)
            s += '\t' +  str(frestdy)
            s += '\t' +  str(frestdxp)
            s += '\t' +  str(frestdyp) + '\n'
            stdout.writelines(h)
            stdout.writelines(s)
        stdout.close()

        #Optical function beta plot
        madx = pymadx.Tfs(''+self.tfsfilename+'.tfs')
        Ms = madx.GetColumn('S')
        Mbetx = madx.GetColumn('BETX') 
        Mbety = madx.GetColumn('BETY')

        bdsim = robdsim.robdsimOutput(''+self.filename+'.root')
        bdsim.CalculateOpticalFunctions(''+self.filename+'_optics.dat')
        bdata = pybdsim.Data.Load(''+self.filename+'_optics.dat')
        Bs    = bdata.S()
        Bbetx = bdata.Beta_x()
        Bbety = bdata.Beta_y()

        _plt.figure(self.figureNr)
        _plt.clf()
        _plt.plot(Ms,Mbetx,'.',color='r',linestyle='solid',label=r'$\beta_{x}$MDX')
        _plt.plot(Ms,Mbety,'.',color='b',linestyle='solid',label=r'$\beta_{y}$MDX')
        _plt.plot(Bs,Bbetx,'.',color='r',linestyle='dashed',label=r'$\beta_{x}$BDS')
        _plt.plot(Bs,Bbety,'.',color='b',linestyle='dashed',label=r'$\beta_{y}$BDS')
        _plt.title(r'Plot of $\beta_{x,y}$ vs $S$')
        _plt.xlabel(r'$S (m)$')
        _plt.ylabel(r'$\beta_{x,y}(m)$')
        _plt.legend(numpoints=1,loc=7)
        _plt.savefig(self.filename+'_beta.pdf')
        _plt.savefig(self.filename+'_beta.png')

        
        # 2d plots
        #X vs Y
        _plt.figure(self.figureNr+1)
        _plt.clf()
        _plt.plot(Mx,My,'b.',label='PTC')
        _plt.plot(Bx,By,'g.',label='BDSIM')
        if addPrimaries:
            _plt.plot(Bx0,By0,'r.',label='BDSIM prim')
        _plt.legend()
        _plt.xlabel(r"x ($\mu$m)")
        _plt.ylabel(r"y ($\mu$m)")
        _plt.title(self.filename)
        _plt.savefig(self.filename+'_xy.pdf')
        _plt.savefig(self.filename+'_xy.png')

        #XP vs YP
        _plt.figure(self.figureNr+2)
        _plt.clf()
        _plt.plot(Mxp,Myp,'b.',label='PTC')
        _plt.plot(Bxp,Byp,'g.',label='BDSIM')
        if addPrimaries:
            _plt.plot(Bxp0,Byp0,'r.',label='BDSIM prim')
        _plt.legend()
        _plt.xlabel(r"x' ($\mu$m)")
        _plt.ylabel(r"y' ($\mu$m)")
        _plt.title(self.filename)
        _plt.savefig(self.filename+'_xpyp.pdf')
        _plt.savefig(self.filename+'_xpyp.png')

        #X vs XP
        _plt.figure(self.figureNr+3)
        _plt.clf()
        _plt.plot(Mx,Mxp,'b.',label='PTC')
        _plt.plot(Bx,Bxp,'g.',label='BDSIM')
        if addPrimaries:
            _plt.plot(Bx0,Bxp0,'r.',label='BDSIM prim')
        _plt.legend()
        _plt.xlabel(r"x ($\mu$m)")
        _plt.ylabel(r"x' (rad)")
        _plt.title(self.filename)
        _plt.savefig(self.filename+'_xxp.pdf')
        _plt.savefig(self.filename+'_xxp.png')

        #Y vs YP
        _plt.figure(self.figureNr+4)
        _plt.clf()
        _plt.plot(My,Myp,'b.',label='PTC')
        _plt.plot(By,Byp,'g.',label='BDSIM')
        if addPrimaries:
            _plt.plot(By0,Byp,'r.',label='BDSIM prim')
        _plt.legend()
        _plt.xlabel(r"y ($\mu$m)")
        _plt.ylabel(r"y' (rad)")
        _plt.title(self.filename)
        _plt.savefig(self.filename+'_yyp.pdf')
        _plt.savefig(self.filename+'_yyp.png')

        # 1d plots
        # x comparison
        f = _plt.figure(self.figureNr+5)
        f.suptitle(self.filename)
        _plt.clf()

        ax1 = f.add_subplot(221)
        ax1.hist(Mx,color='b',label='PTC',histtype='step')
        ax1.hist(Bx,color='g',label='BDSIM',histtype='step')
        if addPrimaries:
            ax1.hist(Bx0,color='r',label='BDSIM prim',histtype='step')
        ax1.legend(fontsize='x-small',loc=0)
        ax1.set_xlabel(r"x ($\mu$m)")
        
        # y comparison
        ax2 = f.add_subplot(222)
        ax2.hist(My,color='b',label='PTC',histtype='step')
        ax2.hist(By,color='g',label='BDSIM',histtype='step')
        if addPrimaries:
            ax2.hist(By0,color='r',label='BDSIM prim',histtype='step')
        ax2.legend(fontsize='x-small',loc=0)
        ax2.set_xlabel(r"y ($\mu$m)")

        # xp comparison
        ax3 = f.add_subplot(223)
        ax3.hist(Mxp,color='b',label='PTC',histtype='step')
        ax3.hist(Bxp,color='g',label='BDSIM',histtype='step')
        if addPrimaries:
            ax3.hist(Bxp0,color='r',label='BDSIM prim',histtype='step')
        ax3.legend(fontsize='x-small',loc=0)
        ax3.set_xlabel(r"x' (rad)")

        # yp comparison
        ax4 = f.add_subplot(224)
        ax4.hist(Myp,color='b',label='PTC',histtype='step')
        ax4.hist(Byp,color='g',label='BDSIM',histtype='step')
        if addPrimaries:
            ax4.hist(Byp0,color='r',label='BDSIM prim',histtype='step')
        ax4.legend(fontsize='x-small',loc=0)
        ax4.set_xlabel(r"y' (rad)")
        
        _plt.savefig(self.filename+'_hist.pdf')
        _plt.savefig(self.filename+'_hist.png')

        # residuals in one plot
        f = _plt.figure(self.figureNr+9)
        _plt.clf()
        
        axX = f.add_subplot(221)
        axX.hist(Mx,weights=fresx,bins=100,ec='b')
        axX.set_xlabel(r'X ($\mu$m)')
        axX.set_ylabel('Fractional Difference')
        
        axY = f.add_subplot(222)
        axY.hist(My,weights=fresy,bins=100,ec='b')
        axY.set_xlabel(r'Y ($\mu$m)')
        axY.set_ylabel('Fractional Difference')
        
        axXp = f.add_subplot(223)
        axXp.hist(Mxp*1e3,weights=fresxp,bins=100,ec='b')
        axXp.set_xlabel('Xp (mrad)')
        axXp.set_ylabel('Fractional Difference')

        axYp = f.add_subplot(224)
        axYp.hist(Myp*1e3,weights=fresyp,bins=100,ec='b')
        axYp.set_xlabel('Yp (mrad)')
        axYp.set_ylabel('Fractional Diffrence')

        _plt.subplots_adjust(left=0.15,right=0.95,top=0.95,wspace=0.39,hspace=0.25)
        _plt.savefig(self.filename+'_residuals.pdf')
        _plt.savefig(self.filename+'_residuals.png')
        

        #print emittance
        print 'Horizontal emittance bdsim (before,after) ',bdata.Emitt_x()
        print 'Vertical emittance bdsim (before,after) ',bdata.Emitt_y()

        #print stdev fractional errors
        print 'stdFracErrX= ',frestdx,' stdFracErrY= ', frestdy, 'stdFracErrXP= ', frestdxp, 'stdFracErrX= ', frestdyp
        

        if self.usingfolder:
            _os.chdir("../")

        


        

            

        
            


        

    

