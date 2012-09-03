#!/usr/bin/env python
#Tiago de Freitas Pereira <tiagofrepereira@gmail.com>
#Mon Jul 16 08:30:00 CEST 2012

"""This script makes a histogram models for the real accesses videos in REPLAY-ATTACK by averaging the LBP histograms of each real access video for each LBP-TOP plane and it combinations. The output is an hdf5 file with the computed model histograms. The procedure is described in the paper: "LBP-TOP based countermeasure against facial spoofing attacks" - de Freitas Pereira, Tiago and Anjos, Andre and De Martino, Jose Mario and Marcel, Sebastien; ACCV - LBP 2012
"""

import os, sys
import argparse
import bob
import xbob.db.replay
import numpy

def create_full_dataset(files):
  """Creates a full dataset matrix out of all the specified files"""
  dataset = None
  dataset_XY = None
  dataset_XT = None
  dataset_YT = None
  dataset_XT_YT = None
  dataset_XY_XT_YT = None

  dimXY = 0
  dimXT = 0
  dimYT = 0

  for key, filename in files.items():
    filename = os.path.expanduser(filename)
    fvs = bob.io.load(filename)


    if dataset_XY is None:
      #each individual plane
      dimXY = fvs[0][0][0]
      dimXT = fvs[0][0][1]
      dimYT = fvs[0][0][2]

      dataset_XY = numpy.array(fvs[1],copy=True,order='C',dtype='float')
      dataset_XT = numpy.array(fvs[2],copy=True,order='C',dtype='float')
      dataset_YT = numpy.array(fvs[3],copy=True,order='C',dtype='float')

      #Reshaping to the correct dimensions
      dataset_XY = dataset_XY[:,0:dimXY]
      dataset_XT = dataset_XT[:,0:dimXT]
      dataset_YT = dataset_YT[:,0:dimYT]

      #combining the temporal planes
      dataset_XT_YT = numpy.array(numpy.concatenate((dataset_XT,dataset_YT),axis=1),copy=True,order='C',dtype='float')

      #combining the all planes (space + time)
      dataset_XY_XT_YT = numpy.array(numpy.concatenate((dataset_XY,dataset_XT,dataset_YT),axis=1),copy=True,order='C',dtype='float')

    else:
      #appending each individual plane
      dataset_XY = numpy.concatenate((dataset_XY, fvs[1,:,0:dimXY]),axis=0)
      dataset_XT = numpy.concatenate((dataset_XT, fvs[2,:,0:dimXT]),axis=0)
      dataset_YT = numpy.concatenate((dataset_YT, fvs[3,:,0:dimYT]),axis=0)

      #appending temporal frames
      item_XT_YT    = numpy.concatenate((fvs[2,:,0:dimXT],fvs[3,:,0:dimYT]),axis=1)
      dataset_XT_YT = numpy.concatenate((dataset_XT_YT, item_XT_YT),axis=0)

      #appending all frames
      item_XY_XT_YT    = numpy.concatenate((fvs[1,:,0:dimXY],fvs[2,:,0:dimXT],fvs[3,:,0:dimYT]),axis=1)
      dataset_XY_XT_YT = numpy.concatenate((dataset_XY_XT_YT,item_XY_XT_YT),axis=0)
  
  dataset = [dataset_XY,dataset_XT,dataset_YT,dataset_XT_YT,dataset_XY_XT_YT]  
  return dataset

def main():

  basedir = os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0])))

  INPUT_DIR = os.path.join(basedir, 'lbp_features')
  OUTPUT_DIR = os.path.join(basedir, 'res')

  protocols = xbob.db.replay.Database().protocols()
  
  parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('-v', '--input-dir', metavar='DIR', type=str, dest='inputdir', default=INPUT_DIR, help='Base directory containing the histogram features of all the videos')
  parser.add_argument('-d', '--output-dir', metavar='DIR', type=str, dest='outputdir', default=OUTPUT_DIR, help='Base directory that will be used to save the results (models).')
  parser.add_argument('-p', '--protocol', metavar='PROTOCOL', type=str, dest="protocol", default='grandtest', help='The protocol type may be specified instead of the the id switch to subselect a smaller number of files to operate on', choices=protocols)   
  
  args = parser.parse_args()
  if not os.path.exists(args.inputdir):
    parser.error("input directory does not exist")
  
  if not os.path.exists(args.outputdir): # if the output directory doesn't exist, create it
    bob.db.utils.makedirs_safe(args.outputdir)
    
  print "Output directory set to \"%s\"" % args.outputdir
  print "Loading input files..."

  # loading the input files
  db = xbob.db.replay.Database()

  process_train_real = db.files(directory=args.inputdir, extension='.hdf5', protocol=args.protocol, groups='train', cls='real')

  # create the full datasets from the file data
  train_real = create_full_dataset(process_train_real);
  
  models = ['model_hist_real_XY','model_hist_real_XT','model_hist_real_YT','model_hist_real_XT_YT','model_hist_real_XY_XT_YT']
  histmodelsfile = bob.io.HDF5File(os.path.join(args.outputdir, 'histmodelsfile.hdf5'),'w')

  print "Creating the model for each frame and its combinations..."

  for i in range(len(models)):

    print "Creating the model for " + models[i]

    train_real_plane =  train_real[i]

    model_hist_real_plane = numpy.sum(train_real_plane,axis=0,dtype='float64')
    model_hist_real_plane = numpy.divide(model_hist_real_plane,train_real_plane.shape[0])

    print "Saving the model histogram..."
    histmodelsfile.append(models[i], numpy.array(model_hist_real_plane))

  del histmodelsfile
  



 
if __name__ == '__main__':
  main()