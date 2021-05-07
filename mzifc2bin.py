#
# 
# 
#
# Copyright(c) 2021 Jonathan Coles <jonathan.coles@tum.de>
#
# This program is distributed under the GNU GPL v2 license.
# See LICENSE for details.
#

import sys,os
import numpy as np
import scipy as sp 
from scipy.sparse import csr_matrix as sparse_matrix
import argparse
from collections import defaultdict
from itertools import starmap

#
# Escape codes for colored output.
#
class C:
    HEADER    = '\033[95m'
    OKBLUE    = '\033[94m'
    OKGREEN   = '\033[92m'
    WARNING   = '\033[93m'
    FAIL      = '\033[91m'
    ERROR     = '\033[91m'
    ENDC      = '\033[0m'
    BOLD      = '\033[1m'
    UNDERLINE = '\033[4m'

def show(args):

    D = np.load(args.file, allow_pickle=True)
    D = D.item()
    for k,v in D.items():
        nnative = len(v['native'])
        ndecoy  = len(v['decoy'])
        nmodels = nnative + ndecoy
        if isinstance(v, dict):
            print(f'{k}  has {nmodels} models  native=%i  decoy=%i' % (nnative, ndecoy))
        else:
            nr,nc = v[0]['M'][0].shape
            print(f'{k}  has {nmodels} models with {nmatrix} {nr}x{nc} matrices. ')
            for i,m in enumerate(v,1):
                #print(m.keys())
                try:
                    print(f'{k}  MODEL {i}/{nmodels}', m['energy'], m['rmsd'])
                except:
                    print(m)
                    sys.exit(0)

def split(args):

    D = np.load(args.file, allow_pickle=True)
    D = D.item()
    for k,v in D.items():
        nmodels = len(v)
        nmatrix = len(v[0]['M'])
        nr,nc = v[0]['M'][0].shape
        D[k] = dict(native=[], decoy=[])
        for i,m in enumerate(v,1):
            #print(m.keys())
            try:
                #print(f'{k}  MODEL {i}/{nmodels}', m['energy'], m['rmsd'])
                if m['rmsd'] < args.split:
                    D[k]['native'].append(m)
                else:
                    D[k]['decoy' ].append(m)
            except:
                print(m)
                sys.exit(0)
        print(f'{k}  {nmodels} models split %i/%i' % (len(D[k]['native']), len(D[k]['decoy' ])))

    np.save(args.ofile,D)

def main(args):

    if args.show:
        show(args)
        return

    if args.split:
        split(args)
        return


    D = defaultdict(list)

    filesize = os.stat(args.file).st_size

    with open(args.file) as fp:

        skip = False
        pdb = None
        model = None
        matrix = None
        M = []
        nskipped = 0

        curbyte = 0
        for lineno,line in enumerate(fp,1):
            line = line.strip()
            curbyte += len(line)
            if not line: continue


            if len(line) == 4:
                if pdb is not None:
                    if nskipped:
                        print('% 8i%%]  %s  %i models (%i skipped)' % (curbyte / filesize * 100, pdb, len(D[pdb]), nskipped))
                    else:
                        print('% 8i%%]  %s  %i models' % (curbyte / filesize * 100, pdb, len(D[pdb])))

                pdb = line
                nskipped = 0
                continue

            if len(line) >= 4 and line[:5] == 'MODEL':
                mline = line.split()
                if len(mline) != 5:
                    skip = True
                    nskipped += 1
                else:
                    model = dict(energy=float(mline[3]), rmsd=float(mline[4]))
                    skip = False
                M = []
                continue

            if not skip:
                row = list(map(float, line.split()))
                sz = len(row)
                M.append(row)
                if len(M) == 3 * sz:
                    model['M'] = [ sparse_matrix(M[i:i+sz], (sz,sz)) for i in range(0,3*sz,sz) ] 
                    #print(model['M'])
                    D[pdb].append(model)
                    del M

    np.save(args.ofile,D)

def warn(s):
    print(C.WARNING + 'WARNING: ' + s + C.ENDC)

def error(s):
    print(C.ERROR + 'ERROR: ' + s + C.ENDC)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Plot membrane thickness grids as contours.', 
        epilog='Written by Jonathan Coles <jonathan.coles@tum.de>')

    parser.add_argument(
        'file',     help='DAT file(s) to plot.')
    parser.add_argument(
        '-o',       help='Output filename.', metavar='output-file', type=str, dest='ofile')
    parser.add_argument(
        '--show',       help='Display information about binary file ', action='store_true', default=False)
    parser.add_argument(
        '--split',       help='Display information about binary file ', type=float)
    parser.add_argument(
        '--verbose', '-v', help="Set verbose level. Repeated usage increases verbosity.", action='count', default=0)

    args = parser.parse_args()

    if args.verbose >= 3:
        print('Arguments:')
        print(args)

    main(args)
