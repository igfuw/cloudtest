import sys
sys.path.append(".")
sys.path.append("../")
import libmpdata
import numpy as np
import libcloudphxx as libcl
#import analytic_blk_1m_pytest as an
#from constants_pytest import Rd, Rv, cp, p0
import pdb

import matplotlib
#matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import pdb

def test():
    a = np.zeros((10,))
    a[1]=1
    print a
#.5 - l. courant, 3-liczba krokow                                                              
    libmpdata.mpdata(a, 1., 3);
#assert a[1] < 1 and a[2] > 0 #SA - po co ten assert?                                          
    print a


#test()

def plotting(dct):
    nrow = (len(dct)+1)/2
    fig, tpl = plt.subplots(nrows=nrow, ncols=2, figsize=(10,8.5))
    i=0
    for k,v in dct.iteritems():
      tpl[i%nrow,i/nrow].set_title(k)
      tpl[i%nrow,i/nrow].plot(v)
      i+=1
    plt.show()


def libcl_2mom(rho_d, th_d, rv, rc, rr, nc, nr, dt, nx):
    opts = libcl.blk_2m.opts_t()
    opts.acti = True
    opts.cond = True
    opts.acnv = False
    opts.accr = False
    opts.sedi = False
    distr = [{"mean_rd":.04e-6 / 2, "sdev_rd":1.4, "N_stp":60e6, "chem_b":.55}]
           #  {"mean_rd":.15e-6 / 2, "sdev_rd":1.6, "N_stp":40e6, "chem_b":.55}]
    opts.dry_distros = distr

    dot_th = np.zeros((nx,))
    dot_rv = np.zeros((nx,))
    dot_rc = np.zeros((nx,))
    dot_nc = np.zeros((nx,))
    dot_rr = np.zeros((nx,))
    dot_nr = np.zeros((nx,))


    print "qc min, max przed mikro", rc.min(), rc.max()
    print "nc min, max przed mikro", nc.min(), nc.max()
    
    libcl.blk_2m.rhs_cellwise(opts, dot_th, dot_rv, dot_rc, dot_nc, dot_rr, dot_nr,
                              rho_d, th_d, rv, rc, nc, rr, nr, dt)
    
    print "rc min po mikro" ,(rc + dot_rc * dt).min(), (rc + dot_rc * dt).max()
    print "nc min po mikro" ,(nc + dot_nc * dt).min(), (nc + dot_nc * dt).max()

    th_d += dot_th * dt
    rv   += dot_rv * dt
    rc   += dot_rc * dt
    nc   += dot_nc * dt
    rr   += dot_rr * dt
    nr   += dot_nr * dt
    np.place(rc, rc<0, 0)
    np.place(nc, nc<0, 0)
    print "rc min, max po mikro i place", rc.min(), rc.max()
    print "nc min, max po mikro i place", nc.min(), nc.max()

def libcl_1mom(rho_d, th_d, rv, rc, rr, dt):
    opts = libcl.blk_1m.opts_t()
    opts.cond = True
    opts.cevp = True
    opts.revp = False
    opts.conv = False
    opts.accr = False
    opts.sedi = False

    print "1m rc max, min przed mikro", rc.max(), rc.min()
    libcl.blk_1m.adj_cellwise(opts, rho_d, th_d, rv, rc, rr, dt)
    print "1m rc max, min po mikro", rc.max(), rc.min()


def calc_RH(RH, rho_d, th_d, rv):
    for i in range(len(RH)):
	T = libcl.common.T(th_d[i], rho_d[i])
	p = libcl.common.p(rho_d[i], rv[i], T)
	p_v = rho_d[i] * rv[i] * libcl.common.R_v * T
	RH[i] = p_v / libcl.common.p_vs(T)

def main(scheme, nx=300, sl_sg = slice(50,100), crnt=0.1, dt=0.2, nt=300, outfreq=100):
    th_d = np.ones((nx,))* 287.
    rv = np.ones((nx,))* 2.e-3
    rc = np.zeros((nx,))
    rv[sl_sg] += 1.5e-3
    #rc[sl_sg] = 1.e-3 
    rr = np.zeros((nx,))
    rho_d = np.ones((nx,))
    testowa = np.zeros((nx,))
    testowa[sl_sg]= 1.e4

    RH1 = np.empty((nx,))
    RH2 = np.empty((nx,))
    
    var_adv = [th_d, rv, rc, rr, testowa]

    if scheme == "2m":
           nc = np.zeros((nx,))
           #nc[sl_sg] = 1.e8
           nr = np.zeros((nx,))
           var_adv  = var_adv + [nc, nr]

    plotting({"nc":nc, "rc":rc, "rv":rv, "th":th_d, "RH1":RH1, "RH2":RH2})
    for it in range(nt):
        print "it", it

        print "testowa min, max przed adv", testowa.min(), testowa.max()
        if scheme == "2m": print "qc min, max przed adv", rc.min(), rc.max()        
        for var in var_adv:
            libmpdata.mpdata(var, crnt, 1);
        if scheme == "2m": print "qc min, max po adv", rc.min(), rc.max()
        print "testowa min, max po adv", testowa.min(), testowa.max()

        calc_RH(RH1, rho_d, th_d, rv)

        if scheme == "1m":
            libcl_1mom(rho_d, th_d, rv, rc, rr, dt)

        if scheme == "2m":
            #try:
            libcl_2mom(rho_d, th_d, rv, rc, rr, nc, nr, dt, nx)
            #except:
            #    pdb.set_trace()

        calc_RH(RH2, rho_d, th_d, rv) 
                
        print "testowa po it = ", it
        if (it+1) % outfreq == 0:
            plotting({"nc":nc, "rc":rc, "rv":rv, "th":th_d, "RH1":RH1, "RH2":RH2})



main("2m") 
#main("1m") 
